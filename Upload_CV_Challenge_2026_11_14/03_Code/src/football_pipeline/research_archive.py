"""Leest geselecteerde ZIP-onderdelen met gecontroleerde HTTP-rangeverzoeken om volledige corpusdownloads te vermijden."""

from __future__ import annotations

import io
import re
from collections import OrderedDict
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class RangeArchive(io.RawIOBase):
    def __init__(self, url, *, budget_bytes=512 * 1024**2, block_size=256 * 1024):
        """Vraag de grootte van het externe ZIP-bestand op en initialiseer positie en leesbuffer voor
        gecontroleerde HTTP-ranges.
        """
        self.url, self.budget, self.block_size = url, budget_bytes, block_size
        self._effective_url = url
        self.position = self.downloaded = 0
        self.cache = OrderedDict()
        self.size = None
        self._fetch(0, 0)

    def _fetch(self, start, end):
        """Haal uitsluitend het gevraagde bytebereik op en controleer de HTTP-range-uitvoer voordat de
        bytes worden gebruikt.
        """
        expected = end - start + 1
        if self.downloaded + expected > self.budget:
            raise ValueError("Selective archive download exceeds the declared byte budget")
        request = Request(self._effective_url, headers={"Range": f"bytes={start}-{end}"})
        try:
            response = urlopen(request, timeout=60)
        except HTTPError as exc:
            if exc.code not in {401, 403} or self._effective_url == self.url:
                raise
            # Signed download redirects can expire during a large selective run.
            response = urlopen(Request(self.url, headers={"Range": f"bytes={start}-{end}"}), timeout=60)
        with response:
            match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", response.headers.get("Content-Range", ""))
            if response.status != 206 or not match:
                raise ValueError("Archive server did not honor the requested HTTP range")
            first, last, size = map(int, match.groups())
            if (first, last) != (start, end) or (self.size is not None and size != self.size):
                raise ValueError("Archive HTTP range or identity changed")
            body = response.read(expected + 1)
            self.downloaded += len(body)
            if len(body) != expected:
                raise ValueError("Truncated or oversized archive range")
            self.size = size
            if hasattr(response, "geturl"):
                self._effective_url = response.geturl()
            return body

    def readable(self):
        """Meld aan de bestandsinterface dat deze archiefadapter leesbewerkingen ondersteunt."""
        return True

    def seekable(self):
        """Meld dat de ZIP-lezer de positie in het externe archief mag verplaatsen."""
        return True

    def tell(self):
        """Geef de huidige logische bytepositie binnen het externe bestand terug."""
        return self.position

    def seek(self, offset, whence=io.SEEK_SET):
        """Verplaats de logische bytepositie vanaf begin, huidige positie of bestandseinde en geef de
        nieuwe positie terug.
        """
        target = (
            offset
            if whence == io.SEEK_SET
            else self.position + offset
            if whence == io.SEEK_CUR
            else self.size + offset
        )
        if target < 0:
            raise ValueError("Negative archive seek")
        self.position = target
        return target

    def read(self, size=-1):
        """Lever het gevraagde aantal bytes vanaf de huidige positie, gebruik de rangebuffer waar
        mogelijk en schuif de positie op.
        """
        count = (
            max(0, self.size - self.position) if size < 0 else min(size, max(0, self.size - self.position))
        )
        output = bytearray()
        while count:
            block = self.position // self.block_size
            if block not in self.cache:
                start = block * self.block_size
                self.cache[block] = self._fetch(start, min(self.size - 1, start + self.block_size - 1))
                if len(self.cache) > 32:
                    self.cache.popitem(last=False)
            self.cache.move_to_end(block)
            content = self.cache[block]
            offset = self.position % self.block_size
            take = min(count, len(content) - offset)
            output.extend(content[offset : offset + take])
            count -= take
            self.position += take
        return bytes(output)
