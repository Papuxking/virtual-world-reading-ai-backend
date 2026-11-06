"""Ejecutar con el rol migrador antes de iniciar la API con AUTO_MIGRATE=0."""
from database import engine
from esquema import preparar_base

if __name__ == '__main__':
    preparar_base(engine)
    print('Migraciones completadas')
