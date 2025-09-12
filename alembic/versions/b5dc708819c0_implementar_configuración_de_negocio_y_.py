"""Implementar configuración de negocio y asignación por local

Revision ID: b5dc708819c0
Revises: 471b627fcf81
Create Date: 2025-09-02 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5dc708819c0'
down_revision: Union[str, Sequence[str], None] = '471b627fcf81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Comandos generados por Alembic, ajustados manualmente ###
    op.create_table('metodos_pago_local',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('local_id', sa.Integer(), nullable=False),
    sa.Column('nombre_metodo', sa.String(length=50), nullable=False),
    sa.Column('datos_adicionales', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['local_id'], ['locales.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_metodos_pago_local_id'), 'metodos_pago_local', ['id'], unique=False)
    
    op.create_table('producto_locales',
    sa.Column('producto_id', sa.Integer(), nullable=False),
    sa.Column('local_id', sa.Integer(), nullable=False),
    sa.Column('disponible', sa.Boolean(), nullable=False),
    sa.Column('precio_local', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.ForeignKeyConstraint(['local_id'], ['locales.id'], ),
    sa.ForeignKeyConstraint(['producto_id'], ['productos.id'], ),
    sa.PrimaryKeyConstraint('producto_id', 'local_id')
    )
    
    # --- CORRECCIÓN CLAVE ---
    # Añadimos la columna con un valor por defecto a nivel de SERVIDOR.
    # Esto le dice a PostgreSQL qué valor usar para las filas existentes.
    op.add_column('negocios', sa.Column('color_primario', sa.String(length=7), nullable=False, server_default='#3B82F6'))
    op.add_column('negocios', sa.Column('logo_url', sa.String(length=255), nullable=True))
    
    op.add_column('locales', sa.Column('telefono_contacto', sa.String(length=20), nullable=True))
    op.add_column('usuarios', sa.Column('local_asignado_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_usuarios_local_asignado', 'usuarios', 'locales', ['local_asignado_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### Comandos generados por Alembic, ajustados ###
    op.drop_constraint('fk_usuarios_local_asignado', 'usuarios', type_='foreignkey')
    op.drop_column('usuarios', 'local_asignado_id')
    op.drop_column('locales', 'telefono_contacto')
    op.drop_column('negocios', 'logo_url')
    op.drop_column('negocios', 'color_primario')
    op.drop_table('producto_locales')
    op.drop_index(op.f('ix_metodos_pago_local_id'), table_name='metodos_pago_local')
    op.drop_table('metodos_pago_local')
    # ### end Alembic commands ###