import reflex as rx

config = rx.Config(
    app_name="massloop_fe",
    tailwind={},
    disable_plugins=[rx.plugins.SitemapPlugin],
)
