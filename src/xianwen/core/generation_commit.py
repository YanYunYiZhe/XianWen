"""把已验证的生成内容原子写入世界状态。"""

import json
from dataclasses import asdict, replace

from xianwen.core.generation_validation import (
    ValidatedCharacter,
    ValidatedEvent,
    ValidatedGeneratedContent,
    ValidatedLocation,
)
from xianwen.core.world_state import (
    CharacterRecord,
    GeneratedContentRecord,
    GeneratedContentStore,
    LocationRecord,
    StateVersionConflictError,
    WorldSnapshot,
    apply_state_transition,
    build_state_transition,
)


class EmptyGeneratedContentError(ValueError):
    """验证内容为空，没有可登记的新内容。"""


class GeneratedContentConflictError(ValueError):
    """生成内容的正式 ID 与当前世界已有内容冲突。"""


def commit_generated_content(
    snapshot: WorldSnapshot,
    bundle: ValidatedGeneratedContent,
    *,
    expected_version: int,
) -> WorldSnapshot:
    """把已验证生成内容原子写入当前世界快照。

    该提交只更新 DynamicWorldState 和状态版本，不推进回合或年份。
    已生成地点和人物同时写入动态记录与 GeneratedContentStore，
    事件写入 GeneratedContentStore。
    """
    _ensure_not_empty(bundle)

    if expected_version != snapshot.core.state_version:
        raise StateVersionConflictError(
            f"Expected version {expected_version}, "
            f"current version is {snapshot.core.state_version}"
        )

    location_records = tuple(
        LocationRecord(
            id=item.id,
            name=item.name,
            description=item.description,
        )
        for item in bundle.locations
    )
    character_records = tuple(
        CharacterRecord(
            id=item.id,
            name=item.name,
            role=item.role,
            description=item.description,
        )
        for item in bundle.characters
    )

    _ensure_ids_available(snapshot, location_records, character_records, bundle)

    generated_locations = tuple(
        _to_generated_record(
            snapshot,
            "location",
            bundle,
            item,
        )
        for item in bundle.locations
    )
    generated_characters = tuple(
        _to_generated_record(
            snapshot,
            "character",
            bundle,
            item,
        )
        for item in bundle.characters
    )
    generated_events = tuple(
        _to_generated_record(
            snapshot,
            "event",
            bundle,
            item,
        )
        for item in bundle.events
    )

    store = snapshot.dynamic.generated_content
    new_store = GeneratedContentStore(
        locations=(*store.locations, *generated_locations),
        characters=(*store.characters, *generated_characters),
        events=(*store.events, *generated_events),
    )

    new_dynamic = replace(
        snapshot.dynamic,
        locations=(*snapshot.dynamic.locations, *location_records),
        characters=(*snapshot.dynamic.characters, *character_records),
        generated_content=new_store,
    )

    transition = build_state_transition(
        snapshot,
        expected_version=expected_version,
        new_dynamic=new_dynamic,
        advance_time=False,
        source="core",
    )
    return apply_state_transition(snapshot, transition)


def _ensure_not_empty(bundle: ValidatedGeneratedContent) -> None:
    """拒绝空包，避免无意义地增加状态版本。"""
    if not (bundle.locations or bundle.characters or bundle.events):
        raise EmptyGeneratedContentError("generated content bundle is empty")


def _ensure_ids_available(
    snapshot: WorldSnapshot,
    location_records: tuple[LocationRecord, ...],
    character_records: tuple[CharacterRecord, ...],
    bundle: ValidatedGeneratedContent,
) -> None:
    """防止手工构造的 bundle 与当前世界 ID 冲突。"""
    existing_location_ids = {item.id for item in snapshot.dynamic.locations}
    existing_character_ids = {item.id for item in snapshot.dynamic.characters}
    existing_generated_ids = {
        item.id
        for item in (
            *snapshot.dynamic.generated_content.locations,
            *snapshot.dynamic.generated_content.characters,
            *snapshot.dynamic.generated_content.events,
        )
    }

    for location in location_records:
        if location.id in existing_location_ids:
            raise GeneratedContentConflictError(
                f"location id already exists: {location.id!r}"
            )
    for character in character_records:
        if character.id in existing_character_ids:
            raise GeneratedContentConflictError(
                f"character id already exists: {character.id!r}"
            )

    for generated_location in bundle.locations:
        if generated_location.id in existing_generated_ids:
            raise GeneratedContentConflictError(
                f"generated content id already exists: {generated_location.id!r}"
            )
    for generated_character in bundle.characters:
        if generated_character.id in existing_generated_ids:
            raise GeneratedContentConflictError(
                f"generated content id already exists: {generated_character.id!r}"
            )
    for event in bundle.events:
        if event.event_id in existing_generated_ids:
            raise GeneratedContentConflictError(
                f"generated content id already exists: {event.event_id!r}"
            )


def _to_generated_record(
    snapshot: WorldSnapshot,
    kind: str,
    bundle: ValidatedGeneratedContent,
    item: ValidatedLocation | ValidatedCharacter | ValidatedEvent,
) -> GeneratedContentRecord:
    """把已验证内容序列化为正式内容元数据。"""
    definition = json.dumps(
        asdict(item),
        ensure_ascii=False,
        sort_keys=True,
    )
    return GeneratedContentRecord(
        id=_bundle_item_id(item),
        kind=kind,
        source_seed_id=bundle.source_seed_id,
        created_turn=snapshot.core.turn,
        generator_version=bundle.generator_version,
        definition=definition,
    )


def _bundle_item_id(
    item: ValidatedLocation | ValidatedCharacter | ValidatedEvent,
) -> str:
    """读取已验证内容的正式 ID。"""
    if isinstance(item, ValidatedEvent):
        return item.event_id
    return item.id
