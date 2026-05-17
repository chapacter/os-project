from typing import Any, Optional, Type


# Что-то вроде центрального дирежера
class World:
    def __init__(self):
        self._entities: list[Any] = []
        self._components: dict[type, dict[Any, Any]] = {}
        self._systems: list["System"] = []
        self._services: dict[type, Any] = {}

    def add_entity(self, entity: Any) -> Any:
        self._entities.append(entity)
        return entity

    def remove_entity(self, entity: Any) -> None:
        if entity in self._entities:
            self._entities.remove(entity)
            for comp_type in list(self._components.keys()):
                self._components[comp_type].pop(entity, None)

    def has_entity(self, entity: Any) -> bool:
        return entity in self._entities

    def get_all_entities(self) -> list[Any]:
        return list(self._entities)

    def add_component(self, entity: Any, component: Any) -> None:
        comp_type = type(component)
        if comp_type not in self._components:
            self._components[comp_type] = {}
        self._components[comp_type][entity] = component

    def remove_component(self, entity: Any, comp_type: type) -> None:
        if comp_type in self._components:
            self._components[comp_type].pop(entity, None)

    def get_component(self, entity: Any, comp_type: type) -> Optional[Any]:
        return self._components.get(comp_type, {}).get(entity)

    def has_component(self, entity: Any, comp_type: type) -> bool:
        return comp_type in self._components and entity in self._components[comp_type]

    def query(self, *comp_types: type) -> list[Any]:
        if not comp_types:
            return list(self._entities)
        result = None
        for comp_type in comp_types:
            entities = set(self._components.get(comp_type, {}).keys())
            if result is None:
                result = entities
            else:
                result &= entities
            if not result:
                return []
        return [e for e in self._entities if e in result]

    def add_system(self, system: "System") -> None:
        self._systems.append(system)

    def remove_system(self, system: "System") -> None:
        if system in self._systems:
            self._systems.remove(system)

    def get_systems(self) -> list["System"]:
        return list(self._systems)

    def add_service(self, service: Any) -> None:
        self._services[type(service)] = service

    def get(self, service_type: Type) -> Any:
        return self._services[service_type]

    def has_service(self, service_type: type) -> bool:
        return service_type in self._services

    def update(self, dt: float) -> None:
        for system in self._systems:
            system.update(dt)

    def clear(self) -> None:
        self._entities.clear()
        self._components.clear()


class System:
    def __init__(self, world: World):
        self.world = world

    def update(self, dt: float) -> None:
        raise NotImplementedError
