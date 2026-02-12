"""muscles and contraindications as separate tables + M2M with exercises

Revision ID: a1b2c3d4e5f6
Revises: 69da7a776931
Create Date: 2026-02-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "a1b2c3d4e5f6"
down_revision = "69da7a776931"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Справочники
    op.create_table(
        "muscles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_muscles_name"), "muscles", ["name"], unique=True)

    op.create_table(
        "contraindications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_contraindications_name"), "contraindications", ["name"], unique=True)

    # 2. Таблицы связей M2M
    op.create_table(
        "exercise_muscles",
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("muscle_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["exercise_id"],
            ["exercises.id"],
            name="fk_exercise_muscles_exercise_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["muscle_id"],
            ["muscles.id"],
            name="fk_exercise_muscles_muscle_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("exercise_id", "muscle_id"),
    )
    op.create_table(
        "exercise_contraindications",
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("contraindication_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["exercise_id"],
            ["exercises.id"],
            name="fk_exercise_contraindications_exercise_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["contraindication_id"],
            ["contraindications.id"],
            name="fk_exercise_contraindications_contraindication_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("exercise_id", "contraindication_id"),
    )

    # 3. Перенос данных из JSON в справочники и связи
    conn = op.get_bind()
    # Уникальные имена мышц из exercises.muscles (JSON array)
    r = conn.execute(
        sa.text("""
            SELECT DISTINCT jsonb_array_elements_text(muscles::jsonb) AS name
            FROM exercises
            WHERE jsonb_array_length(muscles::jsonb) > 0
        """)
    )
    muscle_names = [row[0] for row in r if row[0]]
    for name in muscle_names:
        conn.execute(sa.text("INSERT INTO muscles (name) VALUES (:name) ON CONFLICT (name) DO NOTHING"), {"name": name})

    # Связи упражнение -> мышцы
    r = conn.execute(
        sa.text("""
            SELECT e.id, jsonb_array_elements_text(e.muscles::jsonb) AS muscle_name
            FROM exercises e
            WHERE jsonb_array_length(e.muscles::jsonb) > 0
        """)
    )
    for row in r:
        ex_id, m_name = row[0], row[1]
        if not m_name:
            continue
        mid = conn.execute(sa.text("SELECT id FROM muscles WHERE name = :name"), {"name": m_name}).scalar()
        if mid:
            conn.execute(
                sa.text(
                    "INSERT INTO exercise_muscles (exercise_id, muscle_id) VALUES (:eid, :mid) ON CONFLICT DO NOTHING"
                ),
                {"eid": ex_id, "mid": mid},
            )

    # Уникальные противопоказания из exercises.contraindications
    r = conn.execute(
        sa.text("""
            SELECT DISTINCT jsonb_array_elements_text(contraindications::jsonb) AS name
            FROM exercises
            WHERE contraindications IS NOT NULL
              AND jsonb_typeof(contraindications::jsonb) = 'array'
              AND jsonb_array_length(contraindications::jsonb) > 0
        """)
    )
    contra_names = [row[0] for row in r if row[0]]
    for name in contra_names:
        conn.execute(
            sa.text("INSERT INTO contraindications (name) VALUES (:name) ON CONFLICT (name) DO NOTHING"),
            {"name": name},
        )

    # Связи упражнение -> противопоказания (если в данных были непустые массивы)
    r = conn.execute(
        sa.text("""
            SELECT e.id, jsonb_array_elements_text(e.contraindications::jsonb) AS c_name
            FROM exercises e
            WHERE e.contraindications IS NOT NULL
              AND jsonb_typeof(e.contraindications::jsonb) = 'array'
              AND jsonb_array_length(e.contraindications::jsonb) > 0
        """)
    )
    for row in r:
        ex_id, c_name = row[0], row[1]
        if not c_name:
            continue
        cid = conn.execute(sa.text("SELECT id FROM contraindications WHERE name = :name"), {"name": c_name}).scalar()
        if cid:
            conn.execute(
                sa.text(
                    "INSERT INTO exercise_contraindications (exercise_id, contraindication_id) VALUES (:eid, :cid) ON CONFLICT DO NOTHING"
                ),
                {"eid": ex_id, "cid": cid},
            )

    # 4. Удаление столбцов JSON
    op.drop_column("exercises", "muscles")
    op.drop_column("exercises", "contraindications")


def downgrade() -> None:
    # 1. Вернуть столбцы JSON в exercises
    op.add_column(
        "exercises",
        sa.Column("muscles", postgresql.JSON(astext_type=sa.Text()), server_default=sa.text("'[]'::json"), nullable=False),
    )
    op.add_column(
        "exercises",
        sa.Column(
            "contraindications",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
    )

    # 2. Обратный перенос: из связей собрать JSON массивы
    conn = op.get_bind()
    r = conn.execute(
        sa.text("""
            SELECT e.id,
                   COALESCE(
                     (SELECT json_agg(m.name ORDER BY m.sort_order, m.name)
                      FROM exercise_muscles em
                      JOIN muscles m ON m.id = em.muscle_id
                      WHERE em.exercise_id = e.id),
                     '[]'::json
                   ) AS muscles_json,
                   COALESCE(
                     (SELECT json_agg(c.name ORDER BY c.sort_order, c.name)
                      FROM exercise_contraindications ec
                      JOIN contraindications c ON c.id = ec.contraindication_id
                      WHERE ec.exercise_id = e.id),
                     '[]'::json
                   ) AS contra_json
            FROM exercises e
        """)
    )
    for row in r:
        ex_id, muscles_json, contra_json = row[0], row[1], row[2]
        conn.execute(
            sa.text("UPDATE exercises SET muscles = :m, contraindications = :c WHERE id = :id"),
            {"id": ex_id, "m": muscles_json, "c": contra_json},
        )

    # 3. Удалить таблицы связей и справочников
    op.drop_table("exercise_contraindications")
    op.drop_table("exercise_muscles")
    op.drop_index(op.f("ix_contraindications_name"), table_name="contraindications")
    op.drop_table("contraindications")
    op.drop_index(op.f("ix_muscles_name"), table_name="muscles")
    op.drop_table("muscles")
