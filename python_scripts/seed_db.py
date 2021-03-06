import sqlite3
import json
import csv
import context

import config
sqlite_file = config.DATABASE_URL
backup_sqlite_file = config.DATABASE_BACKUP_URL


def clear_csvs():
    context.csv_helpers.clear_csv(config.VIOLATIONS_CSV_URL)
    context.csv_helpers.clear_csv(config.PERMITS_CSV_URL)
    context.csv_helpers.clear_csv(config.SERVICE_CALLS_CSV_URL)


def create_buildings_data_tables(c):
    print("creating buildings data tables")
    # context.sales_seeds.create_table(c)
    # context.conversions_seeds.create_table(c)
    # context.permit_clusters_seeds.create_table(c)
    # context.permits_seeds.create_table(c)
    # context.evictions_seeds.create_table(c)


def seed_buildings_data(c):
    print("Seeding building data")
    sales_csv = list(csv.reader(open("data/sales_data/csv/nyc_sales_2010-2017.csv")))[1:]
    context.sales_seeds.seed_sales(c, sales_csv)


def seed_buildings(c, conn):
    print("Seeding buildings")

    file = open(config.UNASSIGNED_BUILDINGS_FILE, 'w+')
    file.close()

    mn_building_json = json.load(open(config.MN_BUILDINGS_DATA))
    context.buildings_seeds.seed(c, mn_building_json)
    conn.commit()

    bx_building_json = json.load(open(config.BX_BUILDINGS_DATA))
    context.buildings_seeds.seed(c, bx_building_json)
    conn.commit()

    bk_building_json = json.load(open(config.BK_BUILDINGS_DATA))
    context.buildings_seeds.seed(c, bk_building_json)
    conn.commit()

    qn_building_json = json.load(open(config.QN_BUILDINGS_DATA))
    context.buildings_seeds.seed(c, qn_building_json)
    conn.commit()

    si_building_json = json.load(open(config.SI_BUILDINGS_DATA))
    context.buildings_seeds.seed(c, si_building_json)
    conn.commit()

    # adds total_buildings number to boundary data tables
    context.buildings_seeds.add_counts_to_boundary_data(c)
    conn.commit()

    # seed virtual table
    context.buildings_seeds.seed_virtual_table(c)
    conn.commit()


def seed_boundary_tables(c, conn):
    print("Seeding boundary tables")
    borough_json = json.load(open(config.BOROUGHS_DATA))
    neighborhood_json = json.load(open(config.NEIGHBORHOODS_DATA))
    census_tract_json = json.load(open(config.CENSUS_TRACTS_DATA))

    context.boroughs_seeds.seed(c, borough_json)
    conn.commit()
    context.neighborhoods_seeds.seed(c, neighborhood_json)
    conn.commit()
    context.census_tracts_seeds.seed(c, census_tract_json)
    conn.commit()


def seed_boundary_table_data(c, conn):
    incomes_csv = list(csv.reader(open(config.INCOME_DATA)))[1:]
    rents_csv = list(csv.reader(open(config.RENT_DATA)))[1:]
    racial_makeup_csv = list(csv.reader(open(config.RACE_DATA)))[1:]

    context.incomes_seeds.seed(c, incomes_csv)
    conn.commit()
    context.rents_seeds.seed(c, rents_csv)
    conn.commit()
    context.racial_makeup_seeds.seed(c, racial_makeup_csv)
    conn.commit()


def seed():
    print("Seeding")
    conn = sqlite3.connect(sqlite_file, timeout=10)
    c = conn.cursor()
    c.execute('pragma foreign_keys=on;')
    c.execute('pragma recursive_triggers=on;')

    seed_boundary_tables(c, conn)
    seed_boundary_table_data(c, conn)
    seed_buildings(c, conn)
    # seed_buildings_data(c)
    conn.commit()
    conn.close()


def clear_evictions():
    conn = sqlite3.connect(sqlite_file, timeout=10)
    c = conn.cursor()
    c.execute('pragma foreign_keys=on;')
    c.execute('pragma recursive_triggers=on')
    c.execute('DELETE FROM building_events WHERE eventable=\'{type}\''.format(type="eviction"))
    c.execute('DROP TABLE IF EXISTS {tn}'.format(tn=context.evictions_seeds.table))
    context.evictions_seeds.create_table(c)
    conn.commit()
    conn.close()


def clear_violations():
    conn = sqlite3.connect(backup_sqlite_file, timeout=10)
    c = conn.cursor()
    c.execute('pragma foreign_keys=on;')
    c.execute('pragma recursive_triggers=on')
    c.execute('DELETE FROM building_events WHERE eventable=\'{type}\''.format(type="violation"))
    c.execute('DROP TABLE IF EXISTS {tn}'.format(tn=context.violations_seeds.table))
    context.violations_seeds.create_table(c)
    conn.commit()
    conn.close()


def clear_sales():
    conn = sqlite3.connect(sqlite_file, timeout=10)
    c = conn.cursor()
    c.execute('pragma foreign_keys=on;')
    c.execute('pragma recursive_triggers=on')
    c.execute('DELETE FROM building_events WHERE eventable=\'{type}\''.format(type="sale"))
    c.execute('DROP TABLE IF EXISTS {tn}'.format(tn=context.sales_seeds.table))
    context.sales_seeds.create_table(c)
    conn.commit()
    conn.close()


def clear_conversions():
    conn = sqlite3.connect(sqlite_file, timeout=10)
    c = conn.cursor()
    c.execute('pragma foreign_keys=on;')
    c.execute('pragma recursive_triggers=on')
    c.execute('DELETE FROM building_events WHERE eventable=\'{type}\''.format(type="conversion"))
    c.execute('DROP TABLE IF EXISTS {tn}'.format(tn=context.conversions_seeds.table))
    context.conversions_seeds.create_table(c)
    conn.commit()
    conn.close()


def rename_building_column():
    conn = sqlite3.connect(sqlite_file, timeout=10)
    c = conn.cursor()
    c.execute('PRAGMA foreign_keys=off;')

    print("making backup table")
    c.execute('ALTER TABLE buildings RENAME TO buildings_old;')
    c.execute('DROP INDEX idx_bldg_block_and_lot')
    c.execute('DROP INDEX idx_bldg_census_tract_id')
    c.execute('DROP INDEX idx_bldg_neighborhood_id')
    c.execute('DROP INDEX idx_bldg_borough_id')
    c.execute('DROP INDEX idx_bldg_class')

    c.execute('DROP INDEX idx_bldg_borough_and_residential')
    c.execute('DROP INDEX idx_bldg_neighborhood_and_residential')
    c.execute('DROP INDEX idx_bldg_census_tract_and_residential')

    c.execute('DROP INDEX idx_bldg_boroid_and_address')
    c.execute('DROP INDEX idx_bldg_bbl')

    print("making new table")
    context.buildings_seeds.create_table(c)
    print("seeding new table...")
    c.execute('INSERT INTO buildings (id, borough_id,neighborhood_id,census_tract_id,boro_code,CT2010,bbl,block,lot,address,geometry,representative_point,year_built,residential_units,bldg_class,residential,total_violations,total_sales,total_service_calls,total_service_calls_open_over_month,service_calls_average_days_to_resolve) SELECT * FROM buildings_old;')
    conn.commit()

    c.execute('PRAGMA foreign_keys=on;')


def sample():
    conn = sqlite3.connect(sqlite_file, timeout=10)
    c = conn.cursor()
    c.execute('SELECT * FROM incomes WHERE neighborhood_id=10')
    print(len(c.fetchall()))
    c.execute('pragma foreign_keys=on;')

    # c.execute('SELECT source FROM service_calls WHERE source="HPD"')
    # all_rows = c.fetchall()
    # print(all_rows)
    # c.execute('SELECT * FROM violations')
    # all_rows = c.fetchall()
    # print(len(all_rows))

    # c.execute('SELECT * FROM permits')
    # all_rows = c.fetchall()
    # print(len(all_rows))

    # c.execute('SELECT * FROM service_calls')
    # all_rows = c.fetchall()
    # print(len(all_rows))

    # c.execute('SELECT * FROM sales')
    # all_rows = c.fetchall()
    # print(len(all_rows))
    # print(all_rows[len(all_rows) - 1])
    # for row in all_rows:
    # print(row[1])
    # conn.commit()
    # conn.close()
