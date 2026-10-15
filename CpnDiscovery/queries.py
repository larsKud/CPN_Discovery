db_path = "C:\\Users\\user\\Dokumente\\_data\\UNI\\_MA\\Data\\order-management.sqlite"

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

o2o_sync = "o2o_sync"


import sqlite3
import pandas as pd

def execute_query(query: str, database_file: str = db_path):
    conn = sqlite3.connect(database_file)
    cur = conn.cursor()
    cur.execute(query)
    res =  cur.fetchall()
    cur.close()
    conn.close()
    return res

query = """
    SELECT * FROM event_object
    WHERE ocel_event_id = 'confirm_o-990002'
    ;
"""
get_all_objects = """
    SELECT * FROM object
"""

def execute_update_query(query: str, database_file: str = db_path):
    conn = sqlite3.connect(database_file)
    cur = conn.cursor()
    cur.execute(query)
    conn.commit()
    conn.close()
# go over all object pairs and query their event sets -> form intersection -> if larger then one -> synchronization
# event-object is mainly interesting

def get_all_events_of_object(oid: str):
    query = f"""
    SELECT ocel_event_id FROM event_object
    WHERE ocel_object_id = '{oid}'
"""
    return execute_query(query)


def query_itersection(oid_a: str, oid_b: str):
    query = f"""
SELECT ocel_event_id FROM event_object WHERE ocel_object_id = '{oid_a}'
INTERSECT
SELECT ocel_event_id FROM event_object WHERE ocel_object_id = '{oid_b}';
"""
    return execute_query(query)

def get_types(database_file: str = db_path):
    query = f"""
SELECT DISTINCT {object_type_col} FROM {object_table}
"""
    return [ot[0] for ot in execute_query(query, database_file)]


def build_o2o_table(database_file: str = db_path):
    #drop existing o2o table
    drop_query = f"""
    DROP TABLE IF EXISTS {o2o_sync};
    """
    execute_query(drop_query, database_file)
    query = f"""
CREATE TABLE {o2o_sync} AS
WITH 
-- Step 1: Pre-calculate the total event counts per object per activity type
obj_activity_stats AS (
    SELECT 
        eo.{eo_object_id} AS object_id,
        e.{et_type} AS activity,
        COUNT(DISTINCT e.{et_event_id}) AS total_activity_events
    FROM event_object eo
    JOIN event e ON eo.{eo_event_id} = e.{et_event_id}
    GROUP BY eo.{eo_object_id}, e.{et_type}
),

-- Step 2: Find pairs sharing at least one event AND compute how many events they actually share per activity
shared_event_counts AS (
    SELECT 
        eo1.{eo_object_id} AS obj_a,
        eo2.{eo_object_id} AS obj_b,
        e.{et_type} AS activity,
        COUNT(DISTINCT e.{et_event_id}) AS shared_event_count
    FROM event_object eo1
    JOIN event_object eo2 ON eo1.{eo_event_id} = eo2.{eo_event_id}
    JOIN event e ON eo1.{eo_event_id} = e.{et_event_id}
    WHERE eo1.{eo_object_id} < eo2.{eo_object_id}
    GROUP BY eo1.{eo_object_id}, eo2.{eo_object_id}, e.{et_type}
)

-- Step 3: Match the shared activity counts against total activity counts to classify
SELECT 
    -- 1. Standardize Object IDs
    CASE 
        WHEN o1.{ot_object_type} <= o2.{ot_object_type} THEN sec.obj_a 
        ELSE sec.obj_b 
    END AS obj_a,
    
    -- 2. Standardize Object Types (Alphabetical)
    CASE 
        WHEN o1.{ot_object_type} <= o2.{ot_object_type} THEN o1.{ot_object_type} 
        ELSE o2.{ot_object_type} 
    END AS type_a,
    
    CASE 
        WHEN o1.{ot_object_type} <= o2.{ot_object_type} THEN sec.obj_b 
        ELSE sec.obj_a 
    END AS obj_b,
    
    CASE 
        WHEN o1.{ot_object_type} <= o2.{ot_object_type} THEN o2.{ot_object_type} 
        ELSE o1.{ot_object_type} 
    END AS type_b,
    
    -- 3. Keep Shared Data As-Is
    sec.activity,
    sec.shared_event_count,
    
    -- 4. Standardize Event Counts
    CASE 
        WHEN o1.{ot_object_type} <= o2.{ot_object_type} THEN stats_a.total_activity_events 
        ELSE stats_b.total_activity_events 
    END AS events_a,
    
    CASE 
        WHEN o1.{ot_object_type} <= o2.{ot_object_type} THEN stats_b.total_activity_events 
        ELSE stats_a.total_activity_events 
    END AS events_b,
    NULL as relation

FROM shared_event_counts sec
JOIN obj_activity_stats stats_a ON sec.obj_a = stats_a.object_id AND sec.activity = stats_a.activity
JOIN obj_activity_stats stats_b ON sec.obj_b = stats_b.object_id AND sec.activity = stats_b.activity
JOIN object o1 ON sec.obj_a = o1.{ot_object_id}
JOIN object o2 ON sec.obj_b = o2.{ot_object_id};
"""
    return execute_query(query, database_file)

def extract_type_level_sync(database_file: str = db_path):
    noise_level = 0
    #TODO: Check if: this would discover singular occurences. E.g. just place order would create a synchronization (1 event per object pair)
    query = f"""
    SELECT 
        type_a, 
        type_b, 
        activity,
        SUM(shared_event_count),
        CASE
            -- #s = #a = #b (a<->b)
            WHEN SUM(events_a + events_b - 2*shared_event_count) = 0
                THEN 'A<->B'
            -- #s = #a (a->b)
            WHEN SUM(events_a - shared_event_count) = 0
                THEN 'A->B'
            -- #s = #b (b->a)
            WHEN SUM(events_b - shared_event_count) = 0
                THEN 'A<-B'
            -- #s != #a and != #b (no sync)
            ELSE 'No Sync'
        END as sync_classification
    FROM o2o_sync 
    GROUP BY type_a, type_b, activity
    """
    return execute_query(query, database_file)

def delete_no_sync_from_o2o(database_file: str = db_path) -> None:
    query = f"""
    DELETE FROM o2o_sync
    WHERE shared_event_count <> events_a
        AND shared_event_count <> events_b
"""
    execute_update_query(query, database_file)

def identify_relation_from_o2o(database_file: str = db_path):
    query = f"""
    UPDATE o2o_sync
    SET relation = CASE 
        WHEN events_a = shared_event_count AND events_b = shared_event_count    THEN '<->'
        WHEN events_a = shared_event_count                                      THEN '->'
        WHEN shared_event_count = events_b                                      THEN '<-'
                                                                                ELSE 'No sync'
    END;    
"""
    execute_update_query(query)

def aggregate_activities_and_abstract_to_type(database_file:str = db_path):
    query = f"""
    WITH o2o_aggregated AS (
        SELECT 
            obj_a,
            type_a,
            obj_b,
            type_b,
            STRING_AGG(activity, ',') AS activities,
            SUM(shared_event_count) as shared_event_count,
            SUM(events_a) as events_a,
            SUM(events_b) as events_b,
            CASE 
                WHEN
                    COUNT(DISTINCT activity) = 1 AND MIN(shared_event_count) = 1 THEN CONCAT("Singles ", relation)
                ELSE
                    relation
            END AS relation
        FROM o2o_sync
        GROUP BY obj_a, obj_b, relation
    ) 
    SELECT
        type_a,
        type_b,
        activities,
        SUM(shared_event_count) AS shared_event_count,
        SUM(events_a) as events_a,
        SUM(events_b) as events_b,
        relation
    FROM o2o_aggregated
    GROUP BY type_a, type_b, activities, relation
"""
    return execute_query(query, database_file)

def get_events_counts_of_ots(ot1: str, ot2: str, activities: list[str], database_file: str = db_path):
    # Note this dublicates event counts if multiple objects of the same type are involved
    _activities = ""
    for ac in activities[:-1]:
        _activities += f"\'{ac}\', "
    _activities += f"\'{activities[-1]}\'"
    query = f"""
    SELECT COUNT(*) AS total_relationships
    FROM {event_object} eo1
    -- Join the event table to filter by activity
    JOIN {event_table} ev 
        ON eo1.{eo_event_id} = ev.{et_event_id}
    JOIN {object_table} o1 
        ON eo1.{eo_object_id} = o1.{ot_object_id} 
        AND o1.{ot_object_type} = '{ot1}'
    JOIN {event_object} eo2 
        ON eo1.{eo_event_id} = eo2.{eo_event_id}
    JOIN {object_table} o2 
        ON eo2.{eo_object_id} = o2.{ot_object_id} 
        AND o2.{ot_object_type} = '{ot2}'
    -- Filter for your specific activities
    WHERE ev.{et_type} IN ({_activities});
"""
    return execute_query(query, database_file)

def get_events_count_alternative(ot1: str, ot2: str, activities: list[str], database_file: str = db_path):
    _activities = ""
    for ac in activities[:-1]:
        _activities += f"\'{ac}\', "
    _activities += f"\'{activities[-1]}\'"
    query=f"""
    SELECT COUNT(*) AS total_relationships
    FROM o2o_sync
    WHERE ((type_a = '{ot1}' AND type_b = '{ot2}') OR (type_a = '{ot2}' AND type_b = '{ot1}')) AND activity IN ({_activities});
"""
    return execute_query(query, database_file)


def get_events_count_real_alternative(ot1: str, ot2: str, activities: list[str], database_file: str = db_path):
    _activities = ""
    for ac in activities[:-1]:
        _activities += f"\'{ac}\', "
    _activities += f"\'{activities[-1]}\'"
    query=f"""
WITH
shared_event_counts AS (
    SELECT 
        eo1.{eo_object_id} AS obj_a,
        o1.{ot_object_type} AS type_a,
        eo2.{eo_object_id} AS obj_b,
        o2.{ot_object_type} AS type_b,
        e.{et_type} AS activity,
        COUNT(DISTINCT e.{et_event_id}) AS shared_event_count
    FROM event_object eo1
    JOIN event_object eo2 ON eo1.{eo_event_id} = eo2.{eo_event_id}
    JOIN event e ON eo1.{eo_event_id} = e.{et_event_id}
    JOIN object o1 ON eo1.{eo_object_id} = o1.{ot_object_id}
    JOIN object o2 ON eo2.{eo_object_id} = o2.{ot_object_id}
    WHERE eo1.{eo_object_id} < eo2.{eo_object_id}
    GROUP BY eo1.{eo_object_id}, eo2.{eo_object_id}, e.{et_type}
)
SELECT 
    SUM(shared_event_count) as shared_event_count
FROM shared_event_counts
WHERE ((type_a = '{ot1}' AND type_b = '{ot2}') or (type_a = '{ot2}' AND type_b = '{ot1}')) AND activity IN ({_activities});

"""
    # query was optimized with gemini to improve performance and checked for matching results
    more_performative_generated_query = f"""
WITH 
-- 1. Narrow down objects to only the target types immediately
filtered_objects AS (
    SELECT 
        {ot_object_id}, 
        {ot_object_type}
    FROM object
    WHERE {ot_object_type} IN ('{ot1}', '{ot2}')
),

-- 2. Keep only event-object relationships matching our target activities and objects
filtered_event_objects AS (
    SELECT 
        eo.{eo_object_id}, 
        eo.{eo_event_id}, 
        o.{ot_object_type}, 
        e.{et_type} AS activity
    FROM event_object eo
    JOIN filtered_objects o 
      ON eo.{eo_object_id} = o.{ot_object_id}
    JOIN event e 
      ON eo.{eo_event_id} = e.{et_event_id}
    WHERE e.{et_type} IN ({_activities})
),

-- 3. Self-join only the highly-pruned subset of data
shared_event_counts AS (
    SELECT 
        eo1.{eo_object_id} AS obj_a,
        eo1.{ot_object_type} AS type_a,
        eo2.{eo_object_id} AS obj_b,
        eo2.{ot_object_type} AS type_b,
        eo1.activity,
        COUNT(DISTINCT eo1.{eo_event_id}) AS shared_event_count
    FROM filtered_event_objects eo1
    JOIN filtered_event_objects eo2 
      ON eo1.{eo_event_id} = eo2.{eo_event_id}
     AND eo1.{eo_object_id} < eo2.{eo_object_id}
    WHERE (
        (eo1.{ot_object_type} = '{ot1}' AND eo2.{ot_object_type} = '{ot2}')
        OR 
        (eo1.{ot_object_type} = '{ot2}' AND eo2.{ot_object_type} = '{ot1}')
    )
    GROUP BY eo1.{eo_object_id}, eo2.{eo_object_id}, eo1.activity
)

-- 4. Sum the identical aggregated counts
SELECT 
    SUM(shared_event_count) AS shared_event_count
FROM shared_event_counts;
"""
    return execute_query(query, database_file)


def get_a2o2(database_file: str = db_path):
    query = f"""
    WITH
    activities AS (
        SELECT DISTINCT {event_activity_col} AS activity
        FROM {event_table}
    ),
    object_types AS (
        SELECT DISTINCT {object_type_col} AS object_type
        FROM {object_table}
    )
    SELECT
        a1.activity,
        a2.activity,
        o1.object_type,
        o2.object_type
    FROM activities a1
    CROSS JOIN activities a2
    CROSS JOIN object_types o1
    CROSS JOIN object_types o2
    """
    query = f"""
    WITH
activities AS (
    SELECT DISTINCT {event_activity_col} AS activity
    FROM {event_table}
),
object_types AS (
    SELECT DISTINCT {object_type_col} AS object_type
    FROM {object_table}
)
SELECT
    a1.activity AS activity_1,
    a2.activity AS activity_2,
    o1.object_type AS object_type_1,
    o2.object_type AS object_type_2
FROM activities a1
CROSS JOIN activities a2
CROSS JOIN object_types o1
CROSS JOIN object_types o2
WHERE
    -- Condition 1: a1 has an event linked to both o1.object_type and o2.object_type
    EXISTS (
        SELECT 1
        FROM {event_table} e1
        JOIN {event_object_table_name} eo1_a ON e1.{event_id_col} = eo1_a.{event_object_event_id_col}
        JOIN {object_table} obj1_a ON eo1_a.{event_object_object_id_col} = obj1_a.{object_id_col}
        JOIN {event_object_table_name} eo1_b ON e1.{event_id_col} = eo1_b.{event_object_event_id_col}
        JOIN {object_table} obj1_b ON eo1_b.{event_object_object_id_col} = obj1_b.{object_id_col}
        WHERE e1.{event_activity_col} = a1.activity
          AND obj1_a.{object_type_col} = o1.object_type
          AND obj1_b.{object_type_col} = o2.object_type
    )
    AND
    -- Condition 2: a2 has an event linked to both o1.object_type and o2.object_type
    EXISTS (
        SELECT 1
        FROM {event_table} e2
        JOIN {event_object_table_name} eo2_a ON e2.{event_id_col} = eo2_a.{event_object_event_id_col}
        JOIN {object_table} obj2_a ON eo2_a.{event_object_object_id_col} = obj2_a.{object_id_col}
        JOIN {event_object_table_name} eo2_b ON e2.{event_id_col} = eo2_b.{event_object_event_id_col}
        JOIN {object_table} obj2_b ON eo2_b.{event_object_object_id_col} = obj2_b.{object_id_col}
        WHERE e2.{event_activity_col} = a2.activity
          AND obj2_a.{object_type_col} = o1.object_type
          AND obj2_b.{object_type_col} = o2.object_type
    );
    """
    query = f"""
    WITH activity_pair_links AS (
    -- Find all (activity, o1, o2) tuples supported by at least one single event
    SELECT DISTINCT
        e.{event_activity_col} AS activity,
        obj1.{object_type_col} AS object_type_1,
        obj2.{object_type_col} AS object_type_2
    FROM {event_table} e
    JOIN {event_object_table_name} eo1 ON e.{event_id_col} = eo1.{event_object_event_id_col}
    JOIN {object_table} obj1 ON eo1.{event_object_object_id_col} = obj1.{object_id_col}
    JOIN {event_object_table_name} eo2 ON e.{event_id_col} = eo2.{event_object_event_id_col}
    JOIN {object_table} obj2 ON eo2.{event_object_object_id_col} = obj2.{object_id_col}
)
SELECT
    link1.activity AS activity_1,
    link2.activity AS activity_2,
    link1.object_type_1,
    link1.object_type_2
FROM activity_pair_links link1
JOIN activity_pair_links link2
  ON link1.object_type_1 = link2.object_type_1
 AND link1.object_type_2 = link2.object_type_2
 WHERE link1.activity <= link2.activity;
    """
    return execute_query(query, database_file)

def new_synchronization_discovery(
    activity1: str,
    activity2: str,
    type1: str,
    type2: str,
    database_file: str = db_path, 
    alpha: float = 0.5, 
    beta: float = 0.5
):
    query = f"""
    WITH 
    -- 1. Filter events by activity and objects by type
    events_a AS (
        SELECT {event_id_col} AS event_id 
        FROM {event_table_name} 
        WHERE {event_activity_col} = '{activity1}'
    ),
    events_b AS (
        SELECT {event_id_col} AS event_id 
        FROM {event_table_name} 
        WHERE {event_activity_col} = '{activity2}'
    ),
    objects_t1 AS (
        SELECT {object_id_col} AS object_id 
        FROM {object_table_name} 
        WHERE {object_type_col} = '{type1}'
    ),
    objects_t2 AS (
        SELECT {object_id_col} AS object_id 
        FROM {object_table_name} 
        WHERE {object_type_col} = '{type2}'
    ),

    -- 2. Map events to their objects of type t1 and t2
    eo_t1 AS (
        SELECT eo.{event_object_event_id_col} AS event_id, eo.{event_object_object_id_col} AS object_id
        FROM {event_object_table_name} eo
        JOIN objects_t1 t1 ON eo.{event_object_object_id_col} = t1.object_id
    ),
    eo_t2 AS (
        SELECT eo.{event_object_event_id_col} AS event_id, eo.{event_object_object_id_col} AS object_id
        FROM {event_object_table_name} eo
        JOIN objects_t2 t2 ON eo.{event_object_object_id_col} = t2.object_id
    ),

    -- 3. Pre-calculate denominator component of phi: |proj(obj(e), t1) x proj(obj(e), t2)|
    event_pair_counts AS (
        SELECT 
            e1.event_id,
            (COUNT(DISTINCT e1.object_id) * COUNT(DISTINCT e2.object_id)) AS pair_count
        FROM eo_t1 e1
        JOIN eo_t2 e2 ON e1.event_id = e2.event_id
        GROUP BY e1.event_id
    ),

    -- 4. Form candidate event pairs (e1 in a, e2 in b) sharing AT LEAST ONE object of type t1
    candidate_event_pairs AS (
        SELECT DISTINCT
            ea.event_id AS e1_id,
            eb.event_id AS e2_id
        FROM events_a ea
        CROSS JOIN events_b eb
        JOIN eo_t1 e1 ON ea.event_id = e1.event_id
        JOIN eo_t1 e2 ON eb.event_id = e2.event_id AND e1.object_id = e2.object_id
    ),

    -- 5. Calculate numerator of phi: shared (o1, o2) pairs present in both e1 and e2
    shared_object_pairs AS (
        SELECT 
            cep.e1_id,
            cep.e2_id,
            COUNT(DISTINCT e1_t1.object_id || '-' || e1_t2.object_id) AS shared_pair_count
        FROM candidate_event_pairs cep
        JOIN eo_t1 e1_t1 ON cep.e1_id = e1_t1.event_id
        JOIN eo_t1 e2_t1 ON cep.e2_id = e2_t1.event_id AND e1_t1.object_id = e2_t1.object_id
        JOIN eo_t2 e1_t2 ON cep.e1_id = e1_t2.event_id
        JOIN eo_t2 e2_t2 ON cep.e2_id = e2_t2.event_id AND e1_t2.object_id = e2_t2.object_id
        GROUP BY cep.e1_id, cep.e2_id
    ),

    -- 6. Evaluate phi for each candidate event pair against beta
    phi_evaluation AS (
        SELECT 
            sop.e1_id,
            sop.e2_id,
            CASE 
                WHEN (
                    COALESCE(sop.shared_pair_count, 0) * 1.0 / 
                    NULLIF( MIN(c1.pair_count, c2.pair_count), 0)
                ) > {beta} THEN 1 
                ELSE 0 
            END AS phi
        FROM shared_object_pairs sop 
        JOIN event_pair_counts c1 ON sop.e1_id = c1.event_id
        JOIN event_pair_counts c2 ON sop.e2_id = c2.event_id
    ),

    -- 7. Final aggregation to evaluate synchronization against alpha
    synchronization_score AS (
        SELECT 
            SUM(phi) AS num_phi_true,
            COUNT(*) AS total_candidate_pairs,
            (CAST(SUM(phi) AS FLOAT) / NULLIF(COUNT(*), 0)) AS synch_ratio
        FROM phi_evaluation
    )

    SELECT 
        synch_ratio,
        CASE WHEN synch_ratio > {alpha} THEN 1 ELSE 0 END AS is_synchronized
    FROM synchronization_score;
    """
    query_deactivated = f"""
    WITH 
-- 1. Get filtered event-to-object mappings in a single pass per type
eo_t1 AS (
    SELECT 
        eo.{event_object_event_id_col} AS event_id,
        eo.{event_object_object_id_col} AS object_id
    FROM {event_object_table_name} eo
    JOIN {object_table_name} o ON eo.{event_object_object_id_col} = o.{object_id_col}
    JOIN {event_table_name} e ON eo.{event_object_event_id_col} = e.{event_id_col}
    WHERE o.{object_type_col} = '{type1}'
      AND e.{event_activity_col} IN ('{activity1}', '{activity2}')
),
eo_t2 AS (
    SELECT 
        eo.{event_object_event_id_col} AS event_id,
        eo.{event_object_object_id_col} AS object_id
    FROM {event_object_table_name} eo
    JOIN {object_table_name} o ON eo.{event_object_object_id_col} = o.{object_id_col}
    JOIN {event_table_name} e ON eo.{event_object_event_id_col} = e.{event_id_col}
    WHERE o.{object_type_col} = '{type2}'
      AND e.{event_activity_col} IN ('{activity1}', '{activity2}')
),

-- 2. Pre-calculate distinct object counts per event for t1 and t2 independently
t1_counts AS (
    SELECT event_id, COUNT(DISTINCT object_id) AS cnt_t1
    FROM eo_t1 GROUP BY event_id
),
t2_counts AS (
    SELECT event_id, COUNT(DISTINCT object_id) AS cnt_t2
    FROM eo_t2 GROUP BY event_id
),
event_pair_counts AS (
    SELECT 
        c1.event_id,
        (c1.cnt_t1 * c2.cnt_t2) AS pair_count
    FROM t1_counts c1
    JOIN t2_counts c2 ON c1.event_id = c2.event_id
),

-- 3. Discover event pairs (e1 in activity1, e2 in activity2) sharing at least one t1 object
--    and count how many distinct t1 objects they share
shared_t1 AS (
    SELECT 
        e1.event_id AS e1_id,
        e2.event_id AS e2_id,
        COUNT(DISTINCT e1.object_id) AS shared_t1_count
    FROM eo_t1 e1
    JOIN {event_table_name} ea ON e1.event_id = ea.{event_id_col} AND ea.{event_activity_col} = '{activity1}'
    JOIN eo_t1 e2 ON e1.object_id = e2.object_id AND e1.event_id != e2.event_id
    JOIN {event_table_name} eb ON e2.event_id = eb.{event_id_col} AND eb.{event_activity_col} = '{activity2}'
    GROUP BY e1.event_id, e2.event_id
),

-- 4. Count shared t2 objects for those candidate event pairs
shared_t2 AS (
    SELECT 
        st1.e1_id,
        st1.e2_id,
        COUNT(DISTINCT e1.object_id) AS shared_t2_count
    FROM shared_t1 st1
    JOIN eo_t2 e1 ON st1.e1_id = e1.event_id
    JOIN eo_t2 e2 ON st1.e2_id = e2.event_id AND e1.object_id = e2.object_id
    GROUP BY st1.e1_id, st1.e2_id
),

-- 5. Calculate phi (Shared Pairs = shared_t1_count * shared_t2_count)
phi_eval AS (
    SELECT 
        st1.e1_id,
        st1.e2_id,
        CASE 
            WHEN (
                (st1.shared_t1_count * COALESCE(st2.shared_t2_count, 0) * 1.0) / 
                NULLIF(MIN(c1.pair_count, c2.pair_count), 0)
            ) > {beta} THEN 1 
            ELSE 0 
        END AS phi
    FROM shared_t1 st1
    LEFT JOIN shared_t2 st2 ON st1.e1_id = st2.e1_id AND st1.e2_id = st2.e2_id
    JOIN event_pair_counts c1 ON st1.e1_id = c1.event_id
    JOIN event_pair_counts c2 ON st1.e2_id = c2.event_id
)

-- 6. Final ratio evaluation
SELECT 
    synch_ratio,
    CASE WHEN synch_ratio > {alpha} THEN 1 ELSE 0 END AS is_synchronized
FROM (
    SELECT 
        CAST(SUM(phi) AS FLOAT) / NULLIF(COUNT(*), 0) AS synch_ratio
    FROM phi_eval
);
    """
    return execute_query(query, database_file)

def new_synchronization_discovery(
    activity1: str,
    activity2: str,
    type1: str,
    type2: str,
    database_file: str = db_path, 
    alpha: float = 0.5, 
    beta: float = 0.5
):
    # Schema mapping variables
    object_table_name = "object"
    object_id_col = "ocel_id"
    object_type_col = "ocel_type"

    event_table_name = "event"
    event_id_col = "ocel_id"
    event_activity_col = "ocel_type"

    event_object_table_name = "event_object"
    event_object_event_id_col = "ocel_event_id"
    event_object_object_id_col = "ocel_object_id"

    rel_event_pair_counter_part = "COUNT(*)"
    phi_eval_sum_part = "SUM(phi)"
    if activity1 == activity2:
        rel_event_pair_counter_part += "/2"
        phi_eval_sum_part += "/2"

    query = f"""
WITH 
    -- 1. Pre-filter relevant objects
    objects_t1 AS (
        SELECT {object_id_col} AS object_id 
        FROM {object_table_name} 
        WHERE {object_type_col} = '{type1}'
    ),
    objects_t2 AS (
        SELECT {object_id_col} AS object_id 
        FROM {object_table_name} 
        WHERE {object_type_col} = '{type2}'
    ),

    -- 2. Pre-filter event-object relations for fast lookup
    eo_t1 AS (
        SELECT eo.{event_object_event_id_col} AS event_id, eo.{event_object_object_id_col} AS object_id
        FROM {event_object_table_name} eo
        JOIN objects_t1 t1 ON eo.{event_object_object_id_col} = t1.object_id
    ),
    eo_t2 AS (
        SELECT eo.{event_object_event_id_col} AS event_id, eo.{event_object_object_id_col} AS object_id
        FROM {event_object_table_name} eo
        JOIN objects_t2 t2 ON eo.{event_object_object_id_col} = t2.object_id
    ),

    -- 3. Pre-calculate event stats using arithmetic:
    -- Distinct pairs where o1 != o2 is (cnt_t1 * cnt_t2) - cnt_overlap
    event_counts_t1 AS (
        SELECT event_id, COUNT(*) AS cnt_t1 FROM eo_t1 GROUP BY event_id
    ),
    event_counts_t2 AS (
        SELECT event_id, COUNT(*) AS cnt_t2 FROM eo_t2 GROUP BY event_id
    ),
    event_counts_overlap AS (
        SELECT t1.event_id, COUNT(*) AS cnt_overlap
        FROM eo_t1 t1
        JOIN eo_t2 t2 ON t1.event_id = t2.event_id AND t1.object_id = t2.object_id
        GROUP BY t1.event_id
    ),
    event_pair_counts AS (
        SELECT 
            c1.event_id,
            (c1.cnt_t1 * COALESCE(c2.cnt_t2, 0)) - COALESCE(ov.cnt_overlap, 0) AS pair_count
        FROM event_counts_t1 c1
        LEFT JOIN event_counts_t2 c2 ON c1.event_id = c2.event_id
        LEFT JOIN event_counts_overlap ov ON c1.event_id = ov.event_id
    ),

    -- 4. Candidate pairs: e1 in activity1, e2 in activity2, e1 != e2, sharing AT LEAST ONE t1 object
    candidate_event_pairs AS (
        SELECT DISTINCT
            e1.event_id AS e1_id,
            e2.event_id AS e2_id
        FROM eo_t1 e1
        JOIN {event_table_name} ea 
            ON e1.event_id = ea.{event_id_col} AND ea.{event_activity_col} = '{activity1}'
        JOIN eo_t1 e2 
            ON e1.object_id = e2.object_id AND e1.event_id != e2.event_id
        JOIN {event_table_name} eb 
            ON e2.event_id = eb.{event_id_col} AND eb.{event_activity_col} = '{activity2}'
    ),

    -- 5. Calculate shared object intersection directly with math:
    -- shared_pairs = (shared_t1_count * shared_t2_count) - shared_overlap_count
    shared_t1 AS (
        SELECT cep.e1_id, cep.e2_id, COUNT(*) AS cnt_shared_t1
        FROM candidate_event_pairs cep
        JOIN eo_t1 e1 ON cep.e1_id = e1.event_id
        JOIN eo_t1 e2 ON cep.e2_id = e2.event_id AND e1.object_id = e2.object_id
        GROUP BY cep.e1_id, cep.e2_id
    ),
    shared_t2 AS (
        SELECT cep.e1_id, cep.e2_id, COUNT(*) AS cnt_shared_t2
        FROM candidate_event_pairs cep
        JOIN eo_t2 e1 ON cep.e1_id = e1.event_id
        JOIN eo_t2 e2 ON cep.e2_id = e2.event_id AND e1.object_id = e2.object_id
        GROUP BY cep.e1_id, cep.e2_id
    ),
    shared_overlap AS (
        SELECT cep.e1_id, cep.e2_id, COUNT(*) AS cnt_shared_overlap
        FROM candidate_event_pairs cep
        JOIN eo_t1 e1_t1 ON cep.e1_id = e1_t1.event_id
        JOIN eo_t1 e2_t1 ON cep.e2_id = e2_t1.event_id AND e1_t1.object_id = e2_t1.object_id
        JOIN eo_t2 e1_t2 ON cep.e1_id = e1_t2.event_id AND e1_t1.object_id = e1_t2.object_id
        JOIN eo_t2 e2_t2 ON cep.e2_id = e2_t2.event_id AND e1_t2.object_id = e2_t2.object_id
        GROUP BY cep.e1_id, cep.e2_id
    ),
    shared_object_pairs AS (
        SELECT 
            st1.e1_id,
            st1.e2_id,
            (st1.cnt_shared_t1 * COALESCE(st2.cnt_shared_t2, 0)) - COALESCE(so.cnt_shared_overlap, 0) AS shared_pair_count
        FROM shared_t1 st1
        LEFT JOIN shared_t2 st2 ON st1.e1_id = st2.e1_id AND st1.e2_id = st2.e2_id
        LEFT JOIN shared_overlap so ON st1.e1_id = so.e1_id AND st1.e2_id = so.e2_id
    ),

    -- 6. Evaluate phi
    phi_evaluation AS (
        SELECT 
            sop.e1_id,
            sop.e2_id,
            CASE 
                WHEN (
                    COALESCE(sop.shared_pair_count, 0) * 1.0 / 
                    NULLIF(
                        CASE 
                            WHEN c1.pair_count < c2.pair_count THEN c1.pair_count 
                            ELSE c2.pair_count 
                        END, 0
                    )
                ) >= {beta} THEN 1 
                ELSE 0 
            END AS phi
        FROM shared_object_pairs sop 
        LEFT JOIN event_pair_counts c1 ON sop.e1_id = c1.event_id
        LEFT JOIN event_pair_counts c2 ON sop.e2_id = c2.event_id
    ),

    -- 7. Final aggregation
    synchronization_score AS (
        SELECT 
            {phi_eval_sum_part} AS num_phi_true,
            {rel_event_pair_counter_part} AS total_candidate_pairs ,
            CASE
                WHEN {rel_event_pair_counter_part} > 1 THEN
                    (CAST({phi_eval_sum_part} AS FLOAT) / NULLIF({rel_event_pair_counter_part}, 0)) 
                ELSE
                    0
            END AS sync_ratio
        FROM phi_evaluation
    )

SELECT 
    CASE WHEN sync_ratio IS NULL THEN 0.0 ELSE sync_ratio END AS sync_ratio,
    CASE WHEN sync_ratio >= {alpha} THEN 1 ELSE 0 END AS is_synchronized,
    COALESCE(num_phi_true, 0) AS num_phi_true,
    total_candidate_pairs
FROM synchronization_score;
    """
    return execute_query(query, database_file)

def create_performance_indexes(database_file:str = db_path):
    # -- Fast activity filtering
    index_queries = [
        f"""
    CREATE INDEX IF NOT EXISTS idx_event_act 
    ON {event_table_name}({event_activity_col}, {event_id_col});
    """,
    # -- Fast object type filtering
    f"""
    CREATE INDEX IF NOT EXISTS idx_object_type 
    ON {object_table_name}({object_type_col}, {object_id_col});
    """,
    #    -- Two-way composite indexes on the junction table for fast join traversal
    f"""
    CREATE INDEX IF NOT EXISTS idx_eo_event_obj 
    ON {event_object_table_name}({event_object_event_id_col}, {event_object_object_id_col});
    """,
    f"""
    CREATE INDEX IF NOT EXISTS idx_eo_obj_event 
    ON {event_object_table_name}({event_object_object_id_col}, {event_object_event_id_col});
    """
    ]
    for query in index_queries:
        execute_update_query(query, database_file)

def debug_query(
    activity1: str,
    activity2: str,
    type1: str,
    type2: str,
    alpha: float = 0.5, 
    beta: float = 0.5,
    database_file: str = db_path, 
    table: str = ""
):
    # Schema mapping variables
    object_table_name = "object"
    object_id_col = "ocel_id"
    object_type_col = "ocel_type"

    event_table_name = "event"
    event_id_col = "ocel_id"
    event_activity_col = "ocel_type"

    event_object_table_name = "event_object"
    event_object_event_id_col = "ocel_event_id"
    event_object_object_id_col = "ocel_object_id"

    query = f"""
   
    SELECT 
        *
    FROM {table}
    """
    return execute_query(query, database_file)

def is_ressource_type(type1: str, type2: str, threshold: float = 0.5, database_file: str = db_path):
    # Schema mapping variables
    object_table_name = "object"
    object_id_col = "ocel_id"
    object_type_col = "ocel_type"

    event_table_name = "event"
    event_id_col = "ocel_id"
    event_activity_col = "ocel_type"

    event_object_table_name = "event_object"
    event_object_event_id_col = "ocel_event_id"
    event_object_object_id_col = "ocel_object_id"
    
    # switch types
    temp = type1
    type1 = type2
    type2 = temp

    query = f"""
    WITH 
    -- 1. All objects of type1 (|π(O, ot1)|)
    ot1_objects AS (
        SELECT {object_id_col} AS o1_id
        FROM {object_table_name}
        WHERE {object_type_col} = '{type1}'
    ),

    -- 2. Find event-object relations for type1 and type2 with their event activities
    eo1 AS (
        SELECT 
            eo.{event_object_object_id_col} AS o1_id,
            eo.{event_object_event_id_col} AS e1_id,
            e.{event_activity_col} AS activity
        FROM {event_object_table_name} eo
        JOIN {event_table_name} e ON eo.{event_object_event_id_col} = e.{event_id_col}
        JOIN {object_table_name} o ON eo.{event_object_object_id_col} = o.{object_id_col}
        WHERE o.{object_type_col} = '{type1}'
    ),
    eo2 AS (
        SELECT 
            eo.{event_object_object_id_col} AS o2_id,
            eo.{event_object_event_id_col} AS e2_id,
            e.{event_activity_col} AS activity
        FROM {event_object_table_name} eo
        JOIN {event_table_name} e ON eo.{event_object_event_id_col} = e.{event_id_col}
        JOIN {object_table_name} o ON eo.{event_object_object_id_col} = o.{object_id_col}
        WHERE o.{object_type_col} = '{type2}'
    ),

    -- 3. Objects o1 in ot1 that diverge under some o2 in ot2:
    --    There exist e (containing o1 and o2) and e' (same activity, containing o2, NOT containing o1)
    diverging_objects AS (
        SELECT DISTINCT eo1_co.o1_id
        FROM eo1 AS eo1_co
        -- Co-occurrence event e: contains both o1 and o2
        JOIN eo2 AS eo2_co 
          ON eo1_co.e1_id = eo2_co.e2_id
        -- Diverging event e': has same activity, contains o2
        JOIN eo2 AS eo2_div 
          ON eo2_co.o2_id = eo2_div.o2_id 
         AND eo2_co.activity = eo2_div.activity
        -- Ensure o1 does NOT appear in event e'
        WHERE NOT EXISTS (
            SELECT 1 
            FROM {event_object_table_name} eo_check
            WHERE eo_check.{event_object_event_id_col} = eo2_div.e2_id
              AND eo_check.{event_object_object_id_col} = eo1_co.o1_id
        )
    )

    -- 4. Calculate ratio and compare against threshold
    SELECT 
        COALESCE(
            CAST(COUNT(d.o1_id) AS FLOAT) / NULLIF(COUNT(t.o1_id), 0), 
            0
        ) > {threshold} AS is_resource,
        COALESCE(
            CAST(COUNT(d.o1_id) AS FLOAT) / NULLIF(COUNT(t.o1_id), 0), 
            0
        ) AS resource_ratio
        
    FROM ot1_objects t
    LEFT JOIN diverging_objects d ON t.o1_id = d.o1_id;
    """
    query = f"""
    WITH 
-- 1. All objects of type1 (denominator)
ot1_objects AS (
    SELECT {object_id_col} AS o1_id
    FROM {object_table_name}
    WHERE {object_type_col} = '{type1}'
),

-- 2. Objects of type2
ot2_objects AS (
    SELECT {object_id_col} AS o2_id
    FROM {object_table_name}
    WHERE {object_type_col} = '{type2}'
),

-- 3. Pre-filtered event-object pairs with activity to avoid redundant object joins
eo1 AS (
    SELECT 
        eo.{event_object_object_id_col} AS o1_id,
        eo.{event_object_event_id_col} AS e1_id,
        e.{event_activity_col} AS activity
    FROM {event_object_table_name} eo
    JOIN ot1_objects o1 ON eo.{event_object_object_id_col} = o1.o1_id
    JOIN {event_table_name} e ON eo.{event_object_event_id_col} = e.{event_id_col}
),
eo2 AS (
    SELECT 
        eo.{event_object_object_id_col} AS o2_id,
        eo.{event_object_event_id_col} AS e2_id,
        e.{event_activity_col} AS activity
    FROM {event_object_table_name} eo
    JOIN ot2_objects o2 ON eo.{event_object_object_id_col} = o2.o2_id
    JOIN {event_table_name} e ON eo.{event_object_event_id_col} = e.{event_id_col}
),

-- 4. Find diverging o1 objects using EXISTS for faster semi-join short-circuiting
diverging_objects AS (
    SELECT o1.o1_id
    FROM ot1_objects o1
    WHERE EXISTS (
        SELECT 1
        FROM eo1
        JOIN eo2 eo2_co 
          ON eo1.e1_id = eo2_co.e2_id
         AND eo1.o1_id = o1.o1_id
        JOIN eo2 eo2_div 
          ON eo2_co.o2_id = eo2_div.o2_id 
         AND eo1.activity = eo2_div.activity
        WHERE NOT EXISTS (
            SELECT 1 
            FROM {event_object_table_name} eo_check
            WHERE eo_check.{event_object_event_id_col} = eo2_div.e2_id
              AND eo_check.{event_object_object_id_col} = o1.o1_id
        )
    )
)

-- 5. Calculate ratio
SELECT 
    COALESCE(
        CAST(COUNT(d.o1_id) AS FLOAT) / NULLIF(COUNT(t.o1_id), 0), 
        0
    ) > {threshold} AS is_resource,
    COALESCE(
        CAST(COUNT(d.o1_id) AS FLOAT) / NULLIF(COUNT(t.o1_id), 0), 
        0
    ) AS resource_ratio
FROM ot1_objects t
LEFT JOIN diverging_objects d ON t.o1_id = d.o1_id;
    """
    return execute_query(query, database_file)

if __name__ == "__main__":
    
    #res = get_events_counts_of_ots("customers", "items", "confirm order,place order".split(","), database_file=db_path)
    activity1 = "confirm order"
    activity2 = "place order"
    type1 = "orders"
    type2 = "customers"

    if False:
        res = new_synchronization_discovery(
            activity1=activity1,
            activity2=activity2,
            type1=type1,
            type2=type2,        
            database_file=db_path,
            )
    
    print(res)