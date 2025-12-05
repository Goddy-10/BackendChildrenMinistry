from alembic import op
import sqlalchemy as sa


revision = '03d89c07a310'
down_revision = 'fc7f29b8af06'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('attendance') as batch_op:
        
        # Drop ALL anonymous foreign keys
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')

        # Recreate named FKs
        batch_op.create_foreign_key(
            'fk_attendance_child_id_children',
            'children',
            ['child_id'],
            ['id'],
            ondelete='CASCADE'
        )

        batch_op.create_foreign_key(
            'fk_attendance_class_id_sunday_classes',
            'sunday_classes',
            ['class_id'],
            ['id'],
            ondelete='SET NULL'
        )

        batch_op.create_foreign_key(
            'fk_attendance_recorded_by_users',
            'users',
            ['recorded_by'],
            ['id'],
            ondelete='SET NULL'
        )


def downgrade():
    with op.batch_alter_table('attendance') as batch_op:

        # Drop named FKs
        batch_op.drop_constraint('fk_attendance_child_id_children', type_='foreignkey')
        batch_op.drop_constraint('fk_attendance_class_id_sunday_classes', type_='foreignkey')
        batch_op.drop_constraint('fk_attendance_recorded_by_users', type_='foreignkey')

        # Recreate anonymous FKs (no cascade)
        batch_op.create_foreign_key(
            None,
            'children',
            ['child_id'],
            ['id']
        )

        batch_op.create_foreign_key(
            None,
            'sunday_classes',
            ['class_id'],
            ['id']
        )

        batch_op.create_foreign_key(
            None,
            'users',
            ['recorded_by'],
            ['id']
        )