import json
from datetime import datetime
from uuid import uuid4

import pytest

from app.schemas.v2.metadata import (
    AccessControl,
    EventType,
    MetadataEvent,
    MetadataObject,
    MetadataType,
    MetadataVersion,
    generate_content_hash,
)
from app.storage.repository import V2Repository


@pytest.fixture
def repo(tmp_path):
    db_path = tmp_path / "metadata_test.sqlite3"
    repository = V2Repository(db_path)
    return repository


def test_metadata_version_hashing():
    payload = {"key1": "value1", "key2": 123}
    version = MetadataVersion.create(
        object_id="obj-1",
        version_number=1,
        payload=payload,
        created_by="user-1"
    )
    
    # Check hashing is deterministic
    expected_hash = generate_content_hash(payload)
    assert version.content_hash == expected_hash
    assert version.version_number == 1
    assert version.previous_hash is None


def test_repository_save_and_get_metadata(repo: V2Repository):
    payload = {"customer_name": "Test Company", "segment": "Corporate"}
    object_id = str(uuid4())
    
    version1 = MetadataVersion.create(
        object_id=object_id,
        version_number=1,
        payload=payload,
        created_by="system"
    )
    
    event = MetadataEvent(
        object_id=object_id,
        version_id=version1.version_id,
        event_type=EventType.CREATED,
        actor="system",
        context={"reason": "initial load"}
    )
    
    # Save the first version
    obj = repo.save_metadata_version(version1, event)
    
    assert obj.object_id == object_id
    assert obj.current_version_number == 1
    assert obj.current_version_id == version1.version_id
    
    # Fetch object
    fetched_obj = repo.get_metadata_object(object_id)
    assert fetched_obj is not None
    assert fetched_obj.current_version_number == 1
    
    # Fetch version
    fetched_version = repo.get_metadata_version(version1.version_id)
    assert fetched_version is not None
    assert fetched_version.content_hash == version1.content_hash
    assert fetched_version.payload == payload

    # Add second version
    new_payload = {"customer_name": "Test Company", "segment": "Corporate", "status": "Active"}
    version2 = MetadataVersion.create(
        object_id=object_id,
        version_number=2,
        payload=new_payload,
        created_by="system",
        previous_hash=version1.content_hash
    )
    
    repo.save_metadata_version(version2)
    
    # Fetch object again
    updated_obj = repo.get_metadata_object(object_id)
    assert updated_obj.current_version_number == 2
    assert updated_obj.current_version_id == version2.version_id
