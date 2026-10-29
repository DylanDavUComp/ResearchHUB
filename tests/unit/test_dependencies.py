import scramp


def test_scramp_supports_pg8000_ssl_channel_binding() -> None:
    # Sin esta funcion, pg8000 falla al conectar por SSL y el despliegue cae en migrate.
    assert hasattr(scramp, "make_channel_binding")
