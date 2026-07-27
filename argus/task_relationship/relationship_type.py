"""
The RelationshipType enumeration for the ArgusOS Task Relationships
package.

Purpose:
    Represent the closed set of relationship kinds a TaskRelationship
    may describe, per factory/packages/031_TASK_RELATIONSHIPS.md.
    "Do not interpret them. Do not infer behavior." This module
    defines only the enumeration itself; nothing in
    argus.task_relationship or argus.task branches on which
    RelationshipType a given TaskRelationship carries, orders Tasks by
    it, or derives any scheduling/execution consequence from it.
    Mirrors TaskStatus (029)/PlanStatus's own shape: a plain `Enum`
    (not a `str` subclass), values that read naturally as their own
    member name lowercased.

No Interpretation, No Behavior:
    A RelationshipType value is opaque data as far as this codebase's
    own code is concerned - PRECEDES, FOLLOWS, and BLOCKS may read as
    directional or even prescriptive in natural language, but no
    Version 1 code anywhere treats one member differently from
    another. Ordering, dependency resolution, and any actual
    "precedes implies scheduled first" or "blocks implies cannot
    proceed" behavior are explicitly out of scope for this package -
    "This package does not implement scheduling, execution, or
    dependency resolution. It only introduces the relationship
    model."

Responsibilities:
    - RelationshipType: enumerate the four kinds of relationship a
      TaskRelationship's own `relationship_type` field may hold.

Non-Responsibilities:
    - This module implements no interpretation, ordering, or
      validation logic of any kind beyond the enumeration itself.

Dependencies:
    None.
"""

from enum import Enum


class RelationshipType(Enum):
    """
    The closed set of relationship kinds a TaskRelationship may
    describe. None of these members carry any behavior of their own -
    see the module docstring's "No Interpretation, No Behavior" note.

    PRECEDES: the source Task is described as preceding the target
        Task. Purely descriptive - nothing orders execution by it.
    FOLLOWS: the source Task is described as following the target
        Task. Purely descriptive - nothing orders execution by it.
    RELATED: the source and target Tasks are described as related,
        with no further directional or prescriptive meaning. The
        default RelationshipType for a TaskRelationship that has not
        had with_type() called - the most generic, non-committal
        member of this enumeration.
    BLOCKS: the source Task is described as blocking the target Task.
        Purely descriptive - nothing prevents, gates, or reorders
        execution by it.
    """

    PRECEDES = "precedes"
    FOLLOWS = "follows"
    RELATED = "related"
    BLOCKS = "blocks"
