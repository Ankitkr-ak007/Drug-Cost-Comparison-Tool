import reflex as rx
from app.states.medicine_state import MedicineState


def nav_link(label: str, href: str) -> rx.Component:
    return rx.el.a(
        label,
        href=href,
        class_name="text-gray-600 hover:text-blue-600 font-medium transition-colors",
    )


def navbar() -> rx.Component:
    return rx.el.nav(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.icon("shield-plus", class_name="h-8 w-8 text-blue-600"),
                        rx.el.span(
                            "MediSmart",
                            class_name="text-2xl font-bold text-gray-900 tracking-tight",
                        ),
                        class_name="flex items-center gap-2 cursor-pointer",
                        on_click=MedicineState.go_home,
                    ),
                    class_name="flex-shrink-0",
                ),
                rx.el.div(
                    nav_link("Home", "/"),
                    nav_link("MediCompare", "/compare"),
                    nav_link("Upload Prescription", "/upload"),
                    nav_link("Pharmacy Locator", "/locator"),
                    nav_link("Community", "#"),
                    rx.el.a(
                        "MedOS ",
                        rx.el.span(
                            "PRO",
                            class_name="text-[8px] bg-green-100 text-green-700 px-1 py-0.5 rounded font-bold ml-1 align-top",
                        ),
                        href="/medos",
                        class_name="text-green-600 hover:text-green-700 font-bold transition-colors",
                    ),
                    class_name="hidden md:flex items-center space-x-8",
                ),
                rx.el.div(
                    rx.el.button(
                        rx.icon("menu", class_name="h-6 w-6"),
                        on_click=MedicineState.toggle_menu,
                        class_name="md:hidden p-2 text-gray-600 hover:text-blue-600",
                    ),
                    class_name="md:hidden flex items-center",
                ),
                class_name="flex justify-between h-20",
            ),
            rx.cond(
                MedicineState.is_menu_open,
                rx.el.div(
                    rx.el.div(
                        rx.el.a(
                            "Home",
                            href="/",
                            class_name="block px-3 py-2 text-base font-medium text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded-md",
                        ),
                        rx.el.a(
                            "MediCompare",
                            href="/compare",
                            class_name="block px-3 py-2 text-base font-medium text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded-md",
                        ),
                        rx.el.a(
                            "Upload",
                            href="/upload",
                            class_name="block px-3 py-2 text-base font-medium text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded-md",
                        ),
                        rx.el.a(
                            "Locator",
                            href="/locator",
                            class_name="block px-3 py-2 text-base font-medium text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded-md",
                        ),
                        rx.el.a(
                            "MedOS ",
                            rx.el.span(
                                "PRO",
                                class_name="text-[8px] bg-green-100 text-green-700 px-1 py-0.5 rounded font-bold ml-1 align-top",
                            ),
                            href="/medos",
                            class_name="block px-3 py-2 text-base font-bold text-green-600 hover:bg-green-50 hover:text-green-700 rounded-md",
                        ),
                        class_name="px-2 pt-2 pb-3 space-y-1 bg-white border-b",
                    ),
                    class_name="md:hidden",
                ),
            ),
            class_name="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8",
        ),
        class_name="bg-white border-b sticky top-0 z-50 shadow-sm",
    )