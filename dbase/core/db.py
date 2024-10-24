import os.path
import sys

import asyncpg
from aiohttp.web_app import Application
from asyncpg.pool import Pool

from dbase.core.config import settings as st
from dbase.services import commands as cmd


async def create_database_if_not_exists():
    """Создаём БД, если не существует."""
    try:
        connection = await asyncpg.connect(**st.CONNECTION_DATA)
        print(f'Подключено! Необходимая БД {st.POSTGRES_DB} обнаружена')
        await connection.close()
    except:
        connection = await asyncpg.connect(
            host=st.POSTGRES_SERVER,
            port=st.POSTGRES_PORT,
            user='postgres',
            database='template1',
            password='postgres'
        )
        await connection.execute(cmd.CREATE_USER_IF_NOT_EXISTS)
        await connection.execute(cmd.CREATE_DB_IF_NOT_EXISTS)
        print('База создана!')
        await connection.close()
        connection = await asyncpg.connect(**st.CONNECTION_DATA)
        await connection.execute(cmd.CREATE_TABLES)
        print('Таблицы созданы!')
        """For database testing."""
        dirname = os.path.dirname(os.path.abspath(sys.argv[0]))
        tables = ('buildings', 'apartments', 'counters', 'tariffs',
                  'counter_values')
        for table in tables:
            file = os.path.join(dirname, f'core/temp/{table}.csv')
            if table == 'buildings' or table == 'apartments':
                with open(file) as f:
                    data = f.readlines()
                    data_list = [line.strip().split(',') for line in data]
                    if table == 'buildings':
                        for line in data_list:
                            bld_number = (
                                None if line[3] == '' else int(line[3])
                            )
                            await connection.execute(
                                """
                                INSERT INTO buildings (street, house_number,
                                                       bld_number)
                                VALUES ($1, $2, $3);
                                """,
                                line[1], int(line[2]), bld_number
                            )
                    else:
                        for line in data_list:
                            await connection.execute(
                                """
                                INSERT INTO apartments (building, number,
                                                        square)
                                VALUES ($1, $2, $3);
                                """,
                                int(line[1]), int(line[2]), float(line[3])
                            )
            else:
                await connection.execute(cmd.FILL_TABLE.format(table=table,
                                                               file=file))
        await connection.close()
        print('Таблицы заполнены тестовыми данными!')


async def create_database_pool(app: Application):
    """Создание пула для асинхронного подключения к БД."""
    pool: Pool = await asyncpg.create_pool(**st.CONNECTION_DATA,
                                           min_size=6,
                                           max_size=6)
    app[st.DB_KEY] = pool


async def destroy_database_pool(app: Application):
    """Закрытие пула для асинхронного подключения к БД."""
    pool: Pool = app[st.DB_KEY]
    await pool.close()
