import sqlite3

# --- Configuration & Parameterization ---
db_file = "your_event_log.sqlite"  # Path to your .sqlite OCEL 2.0 file
excluded_object_types = ["employees", "products"]

# --- Object Table Parameters ---
object_table_name = "object"
object_id_col = "ocel_id"
object_type_col = "ocel_type"

# --- Event Table Parameters ---
event_table_name = "event"
event_id_col = "ocel_id"
event_activity_col = "ocel_type"  # Activity / event type

# --- Event-Object Relationship Table Parameters ---
event_object_table_name = "event_object"
event_object_event_id_col = "ocel_event_id"
event_object_object_id_col = "ocel_object_id"


def filter_out_object_types(db_path, excluded_types):
    """Removes specified object types and their dependent relationships/tables

    from an OCEL 2.0 SQLite database.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Enforce foreign key checks if enabled, and start transaction
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("BEGIN TRANSACTION;")

        # Create parameterized placeholders for SQL IN clauses
        placeholders = ",".join(["?"] * len(excluded_types))

        # 1. Identify all object IDs belonging to the excluded types
        cursor.execute(
            f"""
            SELECT {object_id_col} 
            FROM {object_table_name} 
            WHERE {object_type_col} IN ({placeholders})
        """,
            excluded_types,
        )
        object_ids_to_remove = [row[0] for row in cursor.fetchall()]

        if object_ids_to_remove:
            id_placeholders = ",".join(["?"] * len(object_ids_to_remove))

            # 2. Delete corresponding rows from Event-Object (E2O) relationship table
            cursor.execute(
                f"""
                DELETE FROM {event_object_table_name}
                WHERE {event_object_object_id_col} IN ({id_placeholders})
            """,
                object_ids_to_remove,
            )

            # 3. Handle Object-to-Object (O2O) relationship table if it exists in the schema
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='object_object';"
            )
            if cursor.fetchone():
                cursor.execute(
                    f"""
                    DELETE FROM object_object
                    WHERE ocel_source_id IN ({id_placeholders}) 
                       OR ocel_target_id IN ({id_placeholders})
                """,
                    object_ids_to_remove + object_ids_to_remove,
                )

            # 4. Delete the objects from the main object table
            cursor.execute(
                f"""
                DELETE FROM {object_table_name}
                WHERE {object_type_col} IN ({placeholders})
            """,
                excluded_types,
            )

        # 5. Clean up OCEL 2.0 type-specific attribute tables and metadata mapping
        for obj_type in excluded_types:
            type_table_name = f"object_{obj_type}"
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
                (type_table_name,),
            )
            if cursor.fetchone():
                cursor.execute(f"DROP TABLE {type_table_name};")

        # 6. Remove types from 'object_corr_type' metadata table if present
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='object_corr_type';"
        )
        if cursor.fetchone():
            corr_placeholders = ",".join(["?"] * len(excluded_types))
            cursor.execute(
                f"""
                DELETE FROM object_corr_type 
                WHERE ocel_type_corr IN ({corr_placeholders})
            """,
                excluded_types,
            )

        # Commit changes
        conn.commit()
        print(
            f"Successfully filtered out object types: {excluded_types} from {db_path}"
        )

    except Exception as e:
        conn.rollback()
        print(f"Error during filtering. Transaction rolled back: {e}")
        raise
    finally:
        conn.close()


# Execute the filtering function
if __name__ == "__main__":
    db_file = "/home/user/Documents/_MA/Data/order-management_lessOT.sqlite"
    excluded_object_types = ["employees", "products"]
    filter_out_object_types(db_file, excluded_object_types)