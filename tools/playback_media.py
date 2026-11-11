"""Fetch a pinned media bundle and copy verified MP4s into the Pages artifact."""
from pathlib import Path, PurePosixPath
from urllib.request import Request, urlopen
import hashlib
import json
import re
import shutil
import uuid
import zipfile


MEDIA_BUDGET = 900 * 1024 * 1024


def sha256(path):
    digest=hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()


def contained_path(base, name):
    path = base / name
    if not path.resolve().is_relative_to(base):
        raise ValueError('Media path escaped its directory: ' + name)
    return path


def materialize_media(root, output, manifest_path):
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    expected={}
    normalized_names=set()
    for record in manifest['records']:
        for kind in ('video','poster'):
            name=record[kind+'_path']
            path=PurePosixPath(name)
            if (path.is_absolute() or '..' in path.parts or path.as_posix()!=name
                    or len(path.parts)<2 or path.parts[0]!='media'
                    or not all(re.fullmatch(r'[A-Za-z0-9_.-]+', part) for part in path.parts)
                    or any(part.endswith('.') for part in path.parts)):
                raise ValueError('Invalid media path: '+name)
            if name.casefold() in normalized_names:raise ValueError('Duplicate media path: '+name)
            normalized_names.add(name.casefold())
            digest=record[kind+'_sha256']
            if not re.fullmatch(r'[0-9a-f]{64}', digest):raise ValueError('Invalid media SHA256: '+name)
            expected[name]=digest
    cache=(root/'.cache/browser-media').resolve()
    output=output.resolve()
    cache.mkdir(parents=True,exist_ok=True)
    def valid(name):
        path=contained_path(cache,name)
        return path.is_file() and sha256(path)==expected[name]
    missing=[name for name in expected if not valid(name)]
    if missing:
        bundle=manifest.get('bundle',{})
        url=bundle.get('url','')
        if not url.startswith('https://github.com/wuxiyang1996/robo-si-review-assets/releases/download/'):
            raise ValueError('Missing pinned public media bundle')
        archive=contained_path(cache,'bundle.zip')
        if not archive.is_file() or sha256(archive)!=bundle['sha256']:
            temporary=contained_path(cache,f'.bundle.{uuid.uuid4().hex}.part')
            try:
                with urlopen(Request(url,headers={'User-Agent':'robo-si-media-builder'}),timeout=90) as response,temporary.open('xb') as target:
                    shutil.copyfileobj(response,target,1024*1024)
                if sha256(temporary)!=bundle['sha256']:
                    raise ValueError('Downloaded media bundle failed SHA256 verification')
                temporary.replace(archive)
            finally:
                temporary.unlink(missing_ok=True)
        with zipfile.ZipFile(archive) as source:
            names=source.namelist()
            if len(names)!=len(set(names)) or set(names)!=set(expected):
                raise ValueError('Media bundle entries differ from the pinned manifest')
            if sum(info.file_size for info in source.infolist())>MEDIA_BUDGET:
                raise ValueError('Media bundle exceeds the Pages media budget')
            for name in missing:
                target=contained_path(cache,name)
                target.parent.mkdir(parents=True,exist_ok=True)
                temporary=contained_path(cache,str(PurePosixPath(name).with_name(f'.{target.name}.{uuid.uuid4().hex}.part')))
                try:
                    with source.open(name) as entry,temporary.open('xb') as handle:
                        shutil.copyfileobj(entry,handle,1024*1024)
                    if sha256(temporary)!=expected[name]:raise ValueError('Media hash mismatch: '+name)
                    temporary.replace(target)
                finally:
                    temporary.unlink(missing_ok=True)
    copies=[(contained_path(cache,name),contained_path(output,name)) for name in expected]
    total=sum(source.stat().st_size for source,_ in copies)
    if total>MEDIA_BUDGET:raise ValueError('Media exceeds the Pages media budget')
    for source,target in copies:
        target.parent.mkdir(parents=True,exist_ok=True)
        temporary=target.with_name(f'.{target.name}.{uuid.uuid4().hex}.part')
        try:
            with source.open('rb') as entry,temporary.open('xb') as handle:
                shutil.copyfileobj(entry,handle,1024*1024)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    print(json.dumps({'browser_media_files':len(expected),'bytes':total}))
    return manifest
