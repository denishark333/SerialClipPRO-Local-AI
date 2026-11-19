"""Serve media without holding Windows file handles while clients pause reading."""
import anyio
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles
from starlette.datastructures import MutableHeaders
from secrets import token_hex


class MediaResponse(FileResponse):
    async def chunks(self, start, end):
        while start < end:
            # Close BEFORE awaiting the network. A paused player must not lock
            # the clip for the lifetime of its HTTP connection.
            def read_chunk():
                with open(self.path, 'rb') as file:
                    file.seek(start)
                    return file.read(min(self.chunk_size, end - start))
            chunk = await anyio.to_thread.run_sync(read_chunk)
            if not chunk:
                raise OSError('Media changed during streaming')
            start += len(chunk)
            yield chunk

    async def _handle_simple(self, send, send_header_only, send_pathsend):
        await send({'type': 'http.response.start', 'status': self.status_code, 'headers': self.raw_headers})
        if not send_header_only:
            async for chunk in self.chunks(0, int(self.headers['content-length'])):
                await send({'type': 'http.response.body', 'body': chunk, 'more_body': True})
        await send({'type': 'http.response.body', 'body': b'', 'more_body': False})

    async def _handle_single_range(self, send, start, end, file_size, send_header_only):
        headers = MutableHeaders(raw=list(self.raw_headers))
        headers['content-range'] = f'bytes {start}-{end - 1}/{file_size}'
        headers['content-length'] = str(end - start)
        await send({'type': 'http.response.start', 'status': 206, 'headers': headers.raw})
        if not send_header_only:
            async for chunk in self.chunks(start, end):
                await send({'type': 'http.response.body', 'body': chunk, 'more_body': True})
        await send({'type': 'http.response.body', 'body': b'', 'more_body': False})

    async def _handle_multiple_ranges(self, send, ranges, file_size, send_header_only):
        boundary = token_hex(13)
        length, header = self.generate_multipart(ranges, boundary, file_size, self.headers['content-type'])
        headers = MutableHeaders(raw=list(self.raw_headers))
        headers['content-type'] = f'multipart/byteranges; boundary={boundary}'
        headers['content-length'] = str(length)
        await send({'type': 'http.response.start', 'status': 206, 'headers': headers.raw})
        if not send_header_only:
            for start, end in ranges:
                await send({'type': 'http.response.body', 'body': header(start, end), 'more_body': True})
                async for chunk in self.chunks(start, end):
                    await send({'type': 'http.response.body', 'body': chunk, 'more_body': True})
                await send({'type': 'http.response.body', 'body': b'\r\n', 'more_body': True})
            await send({'type': 'http.response.body', 'body': f'--{boundary}--'.encode('latin-1'), 'more_body': True})
        await send({'type': 'http.response.body', 'body': b'', 'more_body': False})


class MediaFiles(StaticFiles):
    def file_response(self, full_path, stat_result, scope, status_code=200):
        return MediaResponse(full_path, stat_result=stat_result, status_code=status_code,
                             headers={'Cache-Control': 'no-store'})
