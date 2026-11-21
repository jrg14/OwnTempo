from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleDefinition:
    key: str
    name: str
    description: str
    icon: str
    route_segment: str
    app_label: str | None = None
    available: bool = False


MODULE_CATALOG = (
    ModuleDefinition(
        key="tasks",
        name="Tareas",
        description="Organiza tareas personales o compartidas.",
        icon="check",
        route_segment="tasks",
        app_label="tasks",
        available=True,
    ),
    ModuleDefinition(
        key="shopping",
        name="Lista de compras",
        description="Prepara compras y marca lo que ya está listo.",
        icon="cart",
        route_segment="shopping",
        app_label="shopping",
        available=True,
    ),
    ModuleDefinition(
        key="wishlist",
        name="Lista de deseos",
        description="Guarda productos, experiencias e ideas para más adelante.",
        icon="heart",
        route_segment="wishlist",
        app_label="wishlist",
        available=True,
    ),
    ModuleDefinition(
        key="calendar",
        name="Calendario",
        description="Planifica eventos personales y compartidos.",
        icon="calendar",
        route_segment="calendar",
        app_label="calendar",
        available=True,
    ),
    ModuleDefinition(
        key="expenses",
        name="Gastos",
        description="Separa los movimientos personales de los comunes.",
        icon="wallet",
        route_segment="expenses",
        app_label="expenses",
        available=True,
    ),
)

MODULE_KEYS = tuple(module.key for module in MODULE_CATALOG)
MODULE_CHOICES = tuple((module.key, module.name) for module in MODULE_CATALOG)
MODULES_BY_KEY = {module.key: module for module in MODULE_CATALOG}


def get_module_definition(key):
    return MODULES_BY_KEY.get(key)
