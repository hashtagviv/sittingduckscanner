from bbot.scanner import Scanner
from asyncio import Queue


async def subdomain_enumeration(domain):
    scan = Scanner(domain, presets=["subdomain-enum"])
    async for event in scan.async_start():
        inScopeFound = False
        subFound = False
        for tag in event.tags:
            if tag == "in-scope":
                inScopeFound = True
            if tag == "subdomain":
                subFound = True
        if subFound and inScopeFound:
            print(
                f'found subdomain {event.data}, distance of {event.scope_distance}')
            yield event.data, event.scope_distance
