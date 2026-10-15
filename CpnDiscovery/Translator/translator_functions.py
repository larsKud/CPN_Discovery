class TFunction:
    def __init__(self, name: str, code: str):
        self.name = name
        self.code = code



class Functions:
    @staticmethod
    def get_all_functions(format: str = "ocpn") -> list[str]:
        return [
            Functions.union(format),
            Functions.in1(format),
            Functions.in2(format),
            Functions.remove1(format),
            Functions.remove2(format),
            Functions.get_pairs(format),
            Functions.exists1(format),
            Functions.exists2(format),
            Functions.all_pair_exists(format),
            Functions.imp(format)
        ]

    @staticmethod
    def union(format: str = "ocpn") -> TFunction:
        name = "union"
        if format == "ocpn":
            return TFunction(
                name ,
                """
fn union(list1, list2) {
    let result = list1.extract(0,list1.len);

    for item in list2 {
        if !result.contains(item) {
            result.push(item);
        }
    }

    return result
}
            """)
        else:
            raise NotImplemented(f"Unsupported Format! Got {format}")

    @staticmethod
    def in1(format: str = "ocpn") -> TFunction:
        name = "in1"
        if format == "ocpn":
            return TFunction(
                name ,"""
fn in1(value, list) {
    for tuple in list {
        if tuple[0] == value {
            return true;
        }
    }
    false
}
            """)
        else:
            raise NotImplemented(f"Unsupported Format! Got {format}")

    @staticmethod
    def in2(format: str = "ocpn") -> TFunction:
        name = "in2"
        if format == "ocpn":
            return TFunction(
                name ,"""
fn in2(value, list) {
    for tuple in list {
        if tuple[1] == value {
            return true;
        }
    }
    false
}
            """)
        else:
            raise NotImplemented(f"Unsupported Format! Got {format}")

    @staticmethod
    def remove1(format: str = "ocpn") -> TFunction:
        name = "remove1"
        if format == "ocpn":
            return TFunction(
                name ,"""
fn remove1(values, list) {
    let result = [];
    for tuple in list {
        if tuple[0] !in values {
            result.push(tuple);
        }
    }
    result
}
            """)
        else:
            raise NotImplemented(f"Unsupported Format! Got {format}")
    
    @staticmethod
    def remove2(format: str = "ocpn") -> TFunction:
        name = "remove2"
        if format == "ocpn":
            return TFunction(
                name ,"""
fn remove2(values, list) {
    let result = [];
    for tuple in list {
        if tuple[1] !in values {
            result.push(tuple);
        }
    }
    result
}
            """)
        else:
            raise NotImplemented(f"Unsupported Format! Got {format}")

    @staticmethod
    def get_pairs(format: str = "ocpn") -> TFunction:
        name = "getPairs"
        if format == "ocpn":
            return TFunction(
                name ,"""
fn getPairs(list1, list2) {
    let result = [];

    for item1 in list1 {
        for item2 in list2 {
            result.push([item1, item2]);
        }
    }

    result
}
            """)
        else:
            raise NotImplemented(f"Unsupported Format! Got {format}")

    @staticmethod
    def exists1(format: str = "ocpn") -> TFunction:
        name = "exists1"
        if format == "ocpn":
            return TFunction(
                name ,"""
fn exists1(list1, list_tuples) {
    for x in list1 {
        for tuple in list_tuples {
            if tuple[0] == x {
                return true;
            }
        }
    }

    false
}
                """)
        else:
            raise NotImplemented(f"Unsupported Format! Got {format}")

    @staticmethod
    def exists2(format: str = "ocpn") -> TFunction:
        name = "exists2"
        if format == "ocpn":
            return TFunction(
                name ,"""
fn exists2(list1, list_tuples) {
    for x in list1 {
        for tuple in list_tuples {
            if tuple[1] == x {
                return true;
            }
        }
    }

    false
}
                """)
        else:
            raise NotImplemented(f"Unsupported Format! Got {format}")
    @staticmethod
    def all_pair_exists(format: str = "ocpn") -> TFunction:
        name = "allPairExists"
        if format == "ocpn":
            return TFunction(
                name ,"""
fn allPairExists(x_list, y_list, s_tuples) {
    for x_prime in x_list {
        for y_prime in y_list {
            if !s_tuples.contains([x_prime, y_prime]) {
                return false;
            }
        }
    }

    true
}
                """)
        else:
            raise NotImplemented(f"Unsupported Format! Got {format}")

    @staticmethod
    def imp(format: str = "ocpn") -> TFunction:
        name = "imp"
        if format == "ocpn":
            return TFunction(
                name ,"""
fn imp(a, b) {
    !a || b;
}
                """)
        else:
            raise NotImplemented(f"Unsupported Format! Got {format}")


