import sqlite3
from datetime import datetime
import json
import csv
from CpnDiscovery.queries import get_types, execute_query

object_table = "object"
ot_object_id = "ocel_id"
ot_object_type = "ocel_type"

event_object = "event_object"
eo_event_id = "ocel_event_id"
eo_object_id = "ocel_object_id"

event_table = "event"
et_event_id = "ocel_id"
et_type = "ocel_type"

# --- Object Table ---
object_table_name = "object"
object_id_col = "ocel_id"
object_type_col = "ocel_type"

# --- Event Table ---
event_table_name = "event"
event_id_col = "ocel_id"
event_activity_col = "ocel_type"  # Renamed 'type' -> 'activity' for clarity in OCEL 2.0

# --- Event-Object Relationship Table ---
event_object_table_name = "event_object"
event_object_event_id_col = "ocel_event_id"
event_object_object_id_col = "ocel_object_id"

def compute_events_for_activity(
    db_path: str, 
    activity: str,
) -> int:
    query = f"""
        SELECT COUNT({event_id_col}) 
        FROM {event_table_name} 
        WHERE {event_activity_col} = "{activity}";
    """
    event_count = execute_query(query, database_file=db_path)
    return int(event_count[0][0])

def compute_total_events(
    db_path: str,
) -> int:
    query = f"""
        SELECT COUNT({event_id_col}) 
        FROM {event_table_name};
    """
    total_events = execute_query(query, database_file=db_path)
    return int(total_events[0][0])

def compute_total_objects(
    db_path: str,
) -> int:
    query = f"""
        SELECT COUNT({object_id_col}) 
        FROM {object_table_name};
    """
    total_objects = execute_query(query, database_file=db_path)
    return int(total_objects[0][0])

def compute_average_objects_per_event(
    db_path: str,
) -> float:
    query = f"""
        WITH EventObjectCounts AS (
            SELECT 
                e.{event_id_col} AS event_id,
                COUNT(eo.{event_object_object_id_col}) AS object_count
            FROM {event_table_name} e
            LEFT JOIN {event_object_table_name} eo 
                ON e.{event_id_col} = eo.{event_object_event_id_col}
            GROUP BY e.{event_id_col}
        )
        SELECT AVG(object_count) FROM EventObjectCounts;
    """
    avg_objects = execute_query(query, database_file=db_path)
    return float(avg_objects[0][0])

def compute_objects_per_type(
    db_path: str, 
    object_type: str,
) -> int:
    query = f"""
        SELECT COUNT({object_id_col}) 
        FROM {object_table_name} 
        WHERE {object_type_col} = "{object_type}";
    """
    object_count = execute_query(query, database_file=db_path)
    return int(object_count[0][0])

def compute_average_events_per_object(
    db_path: str, 
    object_type: str,
) -> float:
    
    query = f"""
        WITH ObjectEventCounts AS (
            SELECT 
                o.{object_id_col} AS object_id,
                COUNT(e.{event_object_event_id_col}) AS event_count
            FROM {object_table_name} o
            LEFT JOIN {event_object_table_name} e 
                ON o.{object_id_col} = e.{event_object_object_id_col}
            WHERE o.{object_type_col} = "{object_type}"
            GROUP BY o.{object_id_col}
        )
        SELECT AVG(event_count) FROM ObjectEventCounts;
    """
    avg_events = execute_query(query, database_file=db_path)
    return float(avg_events[0][0])

def get_all_activities(db_path: str) -> list[str]:
    """Retrieves a list of all unique activities (event types) in the event log."""
    query = f"""
        SELECT DISTINCT {event_activity_col} 
        FROM {event_table_name};
    """
    results = execute_query(query, database_file=db_path)  # Assumes your wrapper can fetch all rows
    # Extract strings from the returned rows/tuples
    return [row[0] for row in results]

def get_all_object_types(db_path: str) -> list[str]:
    """Retrieves a list of all unique object types in the object table."""
    query = f"""
        SELECT DISTINCT {object_type_col} 
        FROM {object_table_name};
    """
    results = execute_query(query, database_file=db_path)
    return [row[0] for row in results]

def all_stats(db_path: str) -> dict:
    """Computes statistics for a single OCEL 2.0 database and returns them as a dictionary."""
    stats = {
        "database_path": db_path,
        "total_events": None,
        "total_objects": None,
        "avg_objects_per_event": None,
        "activity_event_counts": {},
        "object_type_stats": {},
        "error": ""
    }
    
    try:
        # --- Global Log Statistics ---
        stats["total_events"] = compute_total_events(db_path)
        stats["total_objects"] = compute_total_objects(db_path)
        stats["avg_objects_per_event"] = compute_average_objects_per_event(db_path)
        
        # --- Per-Activity Statistics ---
        activities = get_all_activities(db_path)
        activity_counts = {}
        for activity in activities:
            activity_counts[activity] = compute_events_for_activity(db_path, activity)
        stats["activity_event_counts"] = activity_counts
            
        # --- Per-Object Type Statistics ---
        object_types = get_all_object_types(db_path)
        obj_stats = {}
        for obj_type in object_types:
            obj_count = compute_objects_per_type(db_path, obj_type)
            avg_events = compute_average_events_per_object(db_path, obj_type)
            obj_stats[obj_type] = {
                "total_objects": obj_count,
                "avg_events_per_object": avg_events
            }
        stats["object_type_stats"] = obj_stats
            
    except Exception as e:
        stats["error"] = str(e)
        
    return stats


def process_databases_to_csv(database_paths: list, output_csv_path: str):
    """Iterates through a list of database paths, computes stats, and saves them to a CSV file."""
    all_results = []
    
    for db_path in database_paths:
        stats = all_stats(db_path)
        
        # Flatten dictionary structure for CSV compatibility
        row = {
            "database_path": stats["database_path"],
            "total_events": stats["total_events"],
            "total_objects": stats["total_objects"],
            "avg_objects_per_event": stats["avg_objects_per_event"],
            "activity_event_counts": json.dumps(stats["activity_event_counts"]),
            "object_type_stats": json.dumps(stats["object_type_stats"]),
            "error": stats["error"]
        }
        all_results.append(row)
        
    # Write results to CSV
    if all_results:
        fieldnames = all_results[0].keys()
        with open(output_csv_path, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)


datasets_stick = [
        "/run/media/user/FA7F-F7F4/_MA/Data/Datasets/order-management.sqlite",
        "/run/media/user/FA7F-F7F4/_MA/Data/Datasets/lrms_01_o2c.sqlite",
        "/run/media/user/FA7F-F7F4/_MA/Data/Datasets/lrms_03_hiring.sqlite",
        "/run/media/user/FA7F-F7F4/_MA/Data/Datasets/lrms_04_hospital.sqlite",
        "/run/media/user/FA7F-F7F4/_MA/Data/Datasets/enron_top_100000.sqlite",
        "/run/media/user/FA7F-F7F4/_MA/Data/Datasets/container_logistics.sqlite"
    ]
datasets_laptop = [
        "/home/user/Documents/_MA/Data/order-management_shortend.sqlite",
        "/home/user/Documents/_MA/Data/order-management.sqlite",
    ]
datasets_pc = [
    "/home/user/Documents/MA_datasets/container_logistics.sqlite",
    "/home/user/Documents/MA_datasets/order-management.sqlite",
    "/home/user/Documents/MA_datasets/ocel2-p2p.sqlite",
    "/home/user/Documents/MA_datasets/lrms_02_p2p.sqlite",
    "/home/user/Documents/MA_datasets/lrms_01_o2c.sqlite",
    "/home/user/Documents/MA_datasets/lrms_03_hiring.sqlite",
    "/home/user/Documents/MA_datasets/lrms_04_hospital.sqlite",
]
datasets = datasets_pc

[
    "/home/user/Documents/MA_datasets/age_of_empires_ocel2.sqlite"
]

if __name__ == "__main__":
    # Example usage configuration
    run_slug = datetime.now().strftime(
        "%y%m%d_%H%M"
    )
    csv_path = f"./Evaluation/Results/db_stats{run_slug}.csv"
    process_databases_to_csv(datasets, csv_path)