from rdflib import Namespace, Literal, Graph, BNode
from rdflib.namespace import RDF, RDFS, OWL, XSD
from rdflib.collection import Collection

MYONT = Namespace("https://ontologeez/")
SCHEMA = Namespace("https://schema.org/")
CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")


def build_ontology(g):
    g.bind("myont", MYONT)
    g.bind("schema", SCHEMA)
    g.bind("crm", CRM)

    ############### CIDOC CLASSES #################################################

    # g.add((CRM.E1_CRM_Entity, RDF.type, OWL.Class))

    g.add((CRM.E22_Human_Made_Object, RDF.type, OWL.Class))
    g.add((CRM.E22_Human_Made_Object, RDFS.label, Literal("Human Made Object")))
    g.add((CRM.E22_Human_Made_Object, RDFS.comment, Literal(
        "A physical object intentionally created by humans, such as artworks, tools, or other manufactured items."
    )))

    # g.add((CRM.E52_Time-Span, RDF.type, OWL.Class))
    # g.add((CRM.E52_Time-Span, RDFS.label, Literal("Time span")))

    g.add((CRM.E39_Actor, RDF.type, OWL.Class))
    g.add((CRM.E39_Actor, RDFS.label, Literal("Actor")))
    g.add((CRM.E39_Actor, RDFS.comment, Literal(
        "An entity capable of performing actions or participating in events, including individuals or groups."
    )))

    g.add((CRM.E21_Person, RDF.type, OWL.Class))
    g.add((CRM.E21_Person, RDFS.label, Literal("Person")))
    g.add((CRM.E21_Person, RDFS.subClassOf, CRM.E39_Actor))
    g.add((CRM.E21_Person, RDFS.comment, Literal(
        "A real human individual, considered as an actor capable of creating, owning, or interacting with objects."
    )))

    g.add((CRM.E53_Place, RDF.type, OWL.Class))
    g.add((CRM.E53_Place, RDFS.label, Literal("Place")))
    g.add((CRM.E53_Place, RDFS.comment, Literal(
        "An extent in space that can serve as the location of physical objects, events, or activities."
    )))

    ###############################################################################

    ############################ SCHEMA CLASSES ####################################

    # g.add((SCHEMA.Thing, RDF.type, OWL.Class))

    g.add((SCHEMA.Painting, RDF.type, OWL.Class))
    g.add((SCHEMA.Painting, RDFS.label, Literal("Painting")))
    g.add((SCHEMA.Painting, RDFS.comment, Literal(
        "A work of visual art created by applying paint to a surface such as canvas, wood, or paper."
    )))
    #  g.add((SCHEMA.Painting, RDFS.subClassOf, CRM.E22_Human_Made_Object))

    g.add((SCHEMA.Sculpture, RDF.type, OWL.Class))
    # with known artist
    g.add((SCHEMA.Sculpture, RDFS.label, Literal("Sculpture")))
    # g.add((SCHEMA.Sculpture, RDFS.subClassOf, CRM.E22_Human_Made_Object))
    g.add((SCHEMA.Sculpture, RDFS.comment, Literal(
        "Any sculpture that has a known artist is included here.")))

    g.add((SCHEMA.Museum, RDF.type, OWL.Class))
    g.add((SCHEMA.Museum, RDFS.label, Literal("Museum")))
    g.add((SCHEMA.Museum, RDFS.comment, Literal(
        "An institution that collects, preserves, studies, and displays objects of artistic, cultural, or historical significance."
    )))

    # only one equivalence statement is necessary
    g.add((SCHEMA.Person, RDF.type, OWL.Class))
    g.add((SCHEMA.Person, RDFS.label, Literal("Person")))
    g.add((SCHEMA.Person, OWL.equivalentClass, CRM.E21_Person))
    g.add((SCHEMA.Person, RDFS.comment, Literal(
        "A human individual."
    )))

    ################################################################################

    ################################ Custom Classes ###############################

    g.add((MYONT.Painting, RDF.type, OWL.Class))
    g.add((MYONT.Painting, RDFS.subClassOf, CRM.E22_Human_Made_Object))
    g.add((MYONT.Painting, RDFS.label, Literal("Painting")))
    g.add((MYONT.Painting, OWL.equivalentClass, SCHEMA.Painting))
    g.add((MYONT.Painting, RDFS.comment, Literal(
        "A painting in the custom ontology, modeled as a human-made object and aligned with schema.org Painting."
    )))

    g.add((MYONT.Sculpture, RDF.type, OWL.Class))
    g.add((MYONT.Sculpture, RDFS.subClassOf, CRM.E22_Human_Made_Object))
    g.add((MYONT.Sculpture, RDFS.label, Literal("Sculpture")))
    g.add((MYONT.Sculpture, OWL.equivalentClass, SCHEMA.Sculpture))
    g.add((MYONT.Sculpture, RDFS.comment, Literal(
        "A sculpture in the custom ontology, modeled as a human-made object and aligned with schema.org Sculpture."
    )))

    g.add((MYONT.Artist, RDF.type, OWL.Class))
    g.add((MYONT.Artist, RDFS.label, Literal("Artist")))
    g.add((MYONT.Artist, RDFS.subClassOf, CRM.E21_Person))
    g.add((MYONT.Artist, RDFS.comment, Literal(
        "A person who creates artworks such as paintings, sculptures, or other museum objects."
    )))
    # g.add((MYONT.Artist, RDFS.subClassOf, SCHEMA.Person))

    g.add((MYONT.Museum, RDF.type, OWL.Class))
    g.add((MYONT.Museum, RDFS.label, Literal("Museum")))
    g.add((MYONT.Museum, OWL.equivalentClass, SCHEMA.Museum))
    g.add((MYONT.Museum, RDFS.comment, Literal(
        "A museum in the custom ontology, aligned with schema.org Museum."
    )))

    # g.add((MYONT.Artifact, RDF.type, OWL.Class))
    # g.add((MYONT.Artifact, RDFS.label, Literal("Artifact"))) # when artist is not known - the thing is more discovered
    # g.add((MYONT.Artifact, RDFS.subClassOf, CRM.E22_Human_Made_Object))

    g.add((MYONT.Vase, RDF.type, OWL.Class))
    g.add((MYONT.Vase, RDFS.label, Literal("Vase")))
    g.add((MYONT.Vase, RDFS.subClassOf, CRM.E22_Human_Made_Object))
    g.add((MYONT.Vase, RDFS.comment, Literal(
        "A human-made container, typically used for holding flowers or as decoration."
    )))

    g.add((MYONT.Ceramic, RDF.type, OWL.Class))
    g.add((MYONT.Ceramic, RDFS.label, Literal("Ceramic")))
    g.add((MYONT.Ceramic, RDFS.subClassOf, CRM.E22_Human_Made_Object))
    g.add((MYONT.Ceramic, RDFS.comment, Literal(
        "A human-made object made from clay or similar material hardened by heat."
    )))

    g.add((MYONT.Jewellery, RDF.type, OWL.Class))
    g.add((MYONT.Jewellery, RDFS.label, Literal("Jewellery")))
    g.add((MYONT.Jewellery, RDFS.subClassOf, CRM.E22_Human_Made_Object))
    g.add((MYONT.Jewellery, RDFS.comment, Literal(
        "A human-made decorative object worn for personal adornment, such as rings, necklaces, or bracelets."
    )))

    g.add((MYONT.Scroll, RDF.type, OWL.Class))
    g.add((MYONT.Scroll, RDFS.label, Literal("Scroll")))
    g.add((MYONT.Scroll, RDFS.subClassOf, CRM.E22_Human_Made_Object))
    g.add((MYONT.Scroll, RDFS.comment, Literal(
        "A rolled written or illustrated document, treated here as a human-made museum object."
    )))

    g.add((MYONT.Statue, RDF.type, OWL.Class))
    g.add((MYONT.Statue, RDFS.label, Literal("Statue")))
    g.add((MYONT.Statue, RDFS.subClassOf, MYONT.Sculpture))
    g.add((MYONT.Statue, RDFS.comment, Literal(
        "A sculpture representing a person, animal, or other figure, typically free-standing."
    )))

    g.add((MYONT.Figurine, RDF.type, OWL.Class))
    g.add((MYONT.Figurine, RDFS.label, Literal("Figurine")))
    g.add((MYONT.Figurine, RDFS.subClassOf, MYONT.Sculpture))
    g.add((MYONT.Figurine, RDFS.comment, Literal(
        "A small sculpted or molded figure representing a human, animal, or mythical being."
    )))

    g.add((MYONT.Theme, RDF.type, OWL.Class))
    g.add((MYONT.Theme, RDFS.label, Literal("Theme")))
    g.add((MYONT.Theme, RDFS.comment, Literal(
        "A subject or conceptual category used to describe the content of an artwork."
    )))

    g.add((MYONT.NatureTheme, RDF.type, OWL.Class))
    g.add((MYONT.NatureTheme, RDFS.label, Literal("Nature theme")))
    g.add((MYONT.NatureTheme, RDFS.subClassOf, MYONT.Theme))
    g.add((MYONT.NatureTheme, RDFS.comment, Literal(
        "A theme representing elements of the natural world, such as landscapes or plants."
    )))

    g.add((MYONT.AnimalTheme, RDF.type, OWL.Class))
    g.add((MYONT.AnimalTheme, RDFS.label, Literal("Animal theme")))
    g.add((MYONT.AnimalTheme, RDFS.subClassOf, MYONT.Theme))
    g.add((MYONT.AnimalTheme, RDFS.comment, Literal(
        "A theme representing animals or animal-related subjects in artworks."
    )))

    g.add((MYONT.ReligiousTheme, RDF.type, OWL.Class))
    g.add((MYONT.ReligiousTheme, RDFS.label, Literal("Religious theme")))
    g.add((MYONT.ReligiousTheme, RDFS.subClassOf, MYONT.Theme))
    g.add((MYONT.ReligiousTheme, RDFS.comment, Literal(
        "A theme representing religious subjects, beliefs, figures, or scenes."
    )))

    g.add((MYONT.MythologicalTheme, RDF.type, OWL.Class))
    g.add((MYONT.MythologicalTheme, RDFS.label, Literal("Mythological theme")))
    g.add((MYONT.MythologicalTheme, RDFS.subClassOf, MYONT.Theme))
    g.add((MYONT.MythologicalTheme, RDFS.comment, Literal(
        "A theme representing mythological figures, stories, or scenes."
    )))

    g.add((MYONT.Department, RDF.type, OWL.Class))
    g.add((MYONT.Department, RDFS.label, Literal("Department")))
    g.add((MYONT.Department, RDFS.comment, Literal(
        "An organizational division within a museum used to group and manage collections or displays."
    )))

    g.add((MYONT.City, RDF.type, OWL.Class))
    g.add((MYONT.City, RDFS.label, Literal("City")))
    g.add((MYONT.City, RDFS.subClassOf, CRM.E53_Place))
    g.add((MYONT.City, RDFS.comment, Literal(
        "A type of place representing a city."
    )))

    g.add((MYONT.Region, RDF.type, OWL.Class))
    g.add((MYONT.Region, RDFS.label, Literal("Region")))
    g.add((MYONT.Region, RDFS.subClassOf, CRM.E53_Place))
    g.add((MYONT.Region, RDFS.comment, Literal(
        "A type of place representing a region."
    )))

    g.add((MYONT.Country, RDF.type, OWL.Class))
    g.add((MYONT.Country, RDFS.label, Literal("Country")))
    g.add((MYONT.Country, RDFS.subClassOf, CRM.E53_Place))
    g.add((MYONT.Country, RDFS.comment, Literal(
        "A type of place representing a country."
    )))

    ############################### AXIOMS #####################################

    g.add((MYONT.City, OWL.disjointWith, MYONT.Country))
    g.add((MYONT.City, OWL.disjointWith, MYONT.Region))
    g.add((MYONT.Country, OWL.disjointWith, MYONT.Region))

    # check if these are correct according to info from structured data source

    g.add((MYONT.Painting, OWL.disjointWith, MYONT.Sculpture))
    g.add((MYONT.Statue, OWL.disjointWith, MYONT.Figurine))
    g.add((MYONT.Painting, OWL.disjointWith, MYONT.Sculpture))
    g.add((MYONT.Painting, OWL.disjointWith, MYONT.Vase))
    g.add((MYONT.Painting, OWL.disjointWith, MYONT.Ceramic))
    g.add((MYONT.Painting, OWL.disjointWith, MYONT.Jewellery))
    g.add((MYONT.Painting, OWL.disjointWith, MYONT.Scroll))
    g.add((MYONT.Sculpture, OWL.disjointWith, MYONT.Scroll))
    g.add((MYONT.Sculpture, OWL.disjointWith, MYONT.Jewellery))
    g.add((MYONT.Vase, OWL.disjointWith, MYONT.Scroll))
    g.add((MYONT.Vase, OWL.disjointWith, MYONT.Jewellery))
    g.add((MYONT.Scroll, OWL.disjointWith, MYONT.Jewellery))

    g.add((MYONT.bornOn, RDF.type, OWL.FunctionalProperty))
    g.add((MYONT.diedOn, RDF.type, OWL.FunctionalProperty))

    g.add((MYONT.createdBy, RDF.type, OWL.AsymmetricProperty))
    g.add((MYONT.displays, RDF.type, OWL.AsymmetricProperty))

    g.add((MYONT.createdBy, RDF.type, OWL.IrreflexiveProperty))
    g.add((MYONT.displays, RDF.type, OWL.IrreflexiveProperty))

    r1 = BNode()
    g.add((r1, RDF.type, OWL.Restriction))
    g.add((r1, OWL.onProperty, MYONT.hasCreated))
    g.add((r1, OWL.minCardinality, Literal(1, datatype=XSD.integer)))
    g.add((MYONT.Artist, RDFS.subClassOf, r1))

    ############################# DEFINED CLASSES ##################################

    # painter
    r_painter = BNode()
    g.add((r_painter, RDF.type, OWL.Restriction))
    g.add((r_painter, OWL.onProperty, MYONT.hasCreated))
    g.add((r_painter, OWL.someValuesFrom, MYONT.Painting))
    intersection_painter = BNode()
    g.add((intersection_painter, RDF.type, OWL.Class))
    col_painter = BNode()
    Collection(g, col_painter, [MYONT.Artist, r_painter])
    g.add((intersection_painter, OWL.intersectionOf, col_painter))
    g.add((MYONT.Painter, RDF.type, OWL.Class))
    g.add((MYONT.Painter, RDFS.label, Literal("Painter")))  # label
    g.add((MYONT.Painter, OWL.equivalentClass, intersection_painter))
    g.add((MYONT.Painter, RDFS.comment, Literal(
        "An artist defined as a person who has created at least one painting."
    )))

    # sculptor
    r_sculptor = BNode()
    g.add((r_sculptor, RDF.type, OWL.Restriction))
    g.add((r_sculptor, OWL.onProperty, MYONT.hasCreated))
    g.add((r_sculptor, OWL.someValuesFrom, MYONT.Sculpture))
    intersection_sculptor = BNode()
    g.add((intersection_sculptor, RDF.type, OWL.Class))
    col_sculptor = BNode()
    Collection(g, col_sculptor, [MYONT.Artist, r_sculptor])
    g.add((intersection_sculptor, OWL.intersectionOf, col_sculptor))
    g.add((MYONT.Sculptor, RDF.type, OWL.Class))
    g.add((MYONT.Sculptor, RDFS.label, Literal("Sculptor")))  # label
    g.add((MYONT.Sculptor, OWL.equivalentClass, intersection_sculptor))
    g.add((MYONT.Sculptor, RDFS.comment, Literal(
        "An artist defined as a person who has created at least one sculpture."
    )))

    # nature oil painting
    r_oil_nature_theme = BNode()
    g.add((r_oil_nature_theme, RDF.type, OWL.Restriction))
    g.add((r_oil_nature_theme, OWL.onProperty, MYONT.hasTheme))
    g.add((r_oil_nature_theme, OWL.someValuesFrom, MYONT.NatureTheme))

    r_oil_nature_medium = BNode()
    g.add((r_oil_nature_medium, RDF.type, OWL.Restriction))
    g.add((r_oil_nature_medium, OWL.onProperty, MYONT.mediumDescription))
    # **********************************
    # data cleaning required for exact match
    g.add((r_oil_nature_medium, OWL.hasValue, Literal("oil", datatype=XSD.string)))

    intersection_nop = BNode()
    g.add((intersection_nop, RDF.type, OWL.Class))
    col_nop = BNode()
    Collection(g, col_nop, [MYONT.Painting,
               r_oil_nature_theme, r_oil_nature_medium])
    g.add((intersection_nop, OWL.intersectionOf, col_nop))

    g.add((MYONT.NatureOilPainting, RDF.type, OWL.Class))
    g.add((MYONT.NatureOilPainting, RDFS.label,
          Literal("Nature oil painting")))  # label
    g.add((MYONT.NatureOilPainting, OWL.equivalentClass, intersection_nop))
    g.add((MYONT.NatureOilPainting, RDFS.comment, Literal(
        "A painting defined as having a nature theme and the medium description 'oil'."
    )))

    # Egyptian animal figurine
    r_theme_eaf = BNode()
    g.add((r_theme_eaf, RDF.type, OWL.Restriction))
    g.add((r_theme_eaf, OWL.onProperty, MYONT.hasTheme))
    g.add((r_theme_eaf, OWL.someValuesFrom, MYONT.AnimalTheme))

    r_culture_eaf = BNode()
    g.add((r_culture_eaf, RDF.type, OWL.Restriction))
    g.add((r_culture_eaf, OWL.onProperty, MYONT.hasCulture))
    # **********************************
    # data cleaning required for exact match - which is why it would be preferred as a class but even if its not, cause too complex - we should have a justification in the report for it
    g.add((r_culture_eaf, OWL.hasValue, Literal("egyptian", datatype=XSD.string)))

    intersection_eaf = BNode()
    g.add((intersection_eaf, RDF.type, OWL.Class))
    col_eaf = BNode()
    Collection(g, col_eaf, [MYONT.Figurine, r_theme_eaf, r_culture_eaf])
    g.add((intersection_eaf, OWL.intersectionOf, col_eaf))

    g.add((MYONT.EgyptianAnimalFigurine, RDF.type, OWL.Class))
    g.add((MYONT.EgyptianAnimalFigurine, RDFS.label,
          Literal("Egyptian animal figurine")))  # label
    g.add((MYONT.EgyptianAnimalFigurine, OWL.equivalentClass, intersection_eaf))
    g.add((MYONT.EgyptianAnimalFigurine, RDFS.comment, Literal(
        "A figurine defined as having an animal theme and the culture value 'egyptian'."
    )))

    # 3d humanmade object

    union_3d = BNode()
    g.add((union_3d, RDF.type, OWL.Class))
    col_3d = BNode()
    Collection(g, col_3d, [MYONT.Sculpture, MYONT.Vase,
               MYONT.Ceramic, MYONT.Jewellery])
    g.add((union_3d, OWL.unionOf, col_3d))
    g.add((MYONT.ThreeDimensionalWork, RDF.type, OWL.Class))
    g.add((MYONT.ThreeDimensionalWork, RDFS.label, Literal(
        "Three-dimensional human-made object")))  # label
    g.add((MYONT.ThreeDimensionalWork, RDFS.subClassOf, CRM.E22_Human_Made_Object))
    g.add((MYONT.ThreeDimensionalWork, OWL.equivalentClass, union_3d))
    g.add((MYONT.ThreeDimensionalWork, RDFS.comment, Literal(
        "A human-made object defined as being either a sculpture, vase, ceramic, or jewellery item."
    )))

    # natural world theme
    union_natural = BNode()
    g.add((union_natural, RDF.type, OWL.Class))
    col_natural = BNode()
    Collection(g, col_natural, [MYONT.NatureTheme, MYONT.AnimalTheme])
    g.add((union_natural, OWL.unionOf, col_natural))
    g.add((MYONT.NaturalWorldTheme, RDF.type, OWL.Class))
    g.add((MYONT.NaturalWorldTheme, RDFS.label,
          Literal("Natural world theme")))  # label
    g.add((MYONT.NaturalWorldTheme, RDFS.subClassOf, MYONT.Theme))
    g.add((MYONT.NaturalWorldTheme, OWL.equivalentClass, union_natural))
    g.add((MYONT.NaturalWorldTheme, RDFS.comment, Literal(
        "A theme defined as either a nature theme or an animal theme."
    )))

    # eva check this please
    # Scroll department only
    r_only_scrolls = BNode()
    g.add((r_only_scrolls, RDF.type, OWL.Restriction))
    g.add((r_only_scrolls, OWL.onProperty, MYONT.departmentDisplays))
    g.add((r_only_scrolls, OWL.allValuesFrom, MYONT.Scroll))

    ###############################################################################

    ############################ SCHEMA.ORG PROPERTIES ####################################

    g.add((SCHEMA.name, RDF.type, OWL.DatatypeProperty))
    g.add((SCHEMA.name, RDFS.range, XSD.string))
    #  g.add((SCHEMA.name, OWL.equivalentProperty, CRM.P102_has_title))
    #  g.add((SCHEMA.name, RDFS.subPropertyOf, CRM.P102_has_title))

    g.add((SCHEMA.dateCreated, RDF.type, OWL.DatatypeProperty))
    g.add((SCHEMA.dateCreated, RDFS.label, Literal("date created")))  # label
    g.add((SCHEMA.dateCreated, RDFS.domain, CRM.E22_Human_Made_Object))
    # use this format for dates in data preprocessing
    g.add((SCHEMA.dateCreated, RDFS.range, XSD.gYear))

    # --------------------------------------------------------------------------------

    g.add((SCHEMA.displayLocation, RDF.type, OWL.ObjectProperty))
    g.add((SCHEMA.displayLocation, RDFS.label, Literal("display location")))
    g.add((SCHEMA.displayLocation, RDFS.domain, CRM.E22_Human_Made_Object))
    g.add((SCHEMA.displayLocation, RDFS.range, CRM.E53_Place))
    g.add((SCHEMA.displayLocation, OWL.equivalentProperty,
          CRM.P55_has_current_location))

    g.add((SCHEMA.locationCreated, RDF.type, OWL.ObjectProperty))
    g.add((SCHEMA.locationCreated, RDFS.label,
          Literal("location created")))  # label
    g.add((SCHEMA.locationCreated, RDFS.domain, CRM.E22_Human_Made_Object))
    g.add((SCHEMA.locationCreated, RDFS.range, CRM.E53_Place))
    # g.add((SCHEMA.locationCreated, RDFS.subPropertyOf, MYONT.createdIn))

    # eva check this please
    g.add((SCHEMA.creator, RDF.type, OWL.ObjectProperty))
    # g.add((SCHEMA.creator, RDFS.domain, CRM.E22_Human_Made_Object))
    # g.add((SCHEMA.creator, RDFS.range, MYONT.Artist))
    # g.add((SCHEMA.creator, OWL.inverseOf, MYONT.hasCreated))

    ###############################################################################

    ############################ CIDOC PROPERTIES ####################################

    g.add((CRM.P55_has_current_location, RDF.type, OWL.ObjectProperty))
    g.add((CRM.P55_has_current_location, RDFS.label,
          Literal("has current location")))  # label
    g.add((CRM.P55_has_current_location, RDFS.domain, CRM.E22_Human_Made_Object))
    g.add((CRM.P55_has_current_location, RDFS.range, CRM.E53_Place))

    g.add((CRM.P102_has_title, RDF.type, OWL.DatatypeProperty))
    g.add((CRM.P102_has_title, RDFS.label, Literal("has title")))  # label
    g.add((CRM.P102_has_title, RDFS.domain, CRM.E22_Human_Made_Object))
    g.add((CRM.P102_has_title, RDFS.range, XSD.string))
    g.add((CRM.P102_has_title, RDFS.subPropertyOf, SCHEMA.name))

    # g.add((CRM.P62_depicts, RDF.type, OWL.DatatypeProperty))
    # g.add((CRM.P62_depicts, RDFS.domain, CRM.E22_Human_Made_Object))
    # g.add((CRM.P62_depicts, RDFS.range, XSD.string))

    # g.add((CRM.P14_carried_out_by, RDF.type, OWL.ObjectProperty))
    # g.add((CRM.P14_carried_out_by, RDFS.domain, CRM.E22_Human_Made_Object))
    # g.add((CRM.P14_carried_out_by, RDFS.range, MYONT.Artist))

    # not an activity for simplification
    g.add((CRM.P108i_was_produced_by, RDF.type, OWL.ObjectProperty))
    g.add((CRM.P108i_was_produced_by, RDFS.label,
          Literal("was produced by")))  # label
    g.add((CRM.P108i_was_produced_by, RDFS.domain, CRM.E22_Human_Made_Object))
    g.add((CRM.P108i_was_produced_by, RDFS.range, CRM.E39_Actor))

    g.add((MYONT.hasDepartment, RDF.type, OWL.ObjectProperty))
    g.add((MYONT.hasDepartment, RDFS.label, Literal("has department")))
    g.add((MYONT.hasDepartment, RDFS.domain, MYONT.Museum))
    g.add((MYONT.hasDepartment, RDFS.range, MYONT.Department))
    g.add((MYONT.hasDepartment, OWL.inverseOf, MYONT.isDepartmentOf))

    g.add((MYONT.isDepartmentOf, RDF.type, OWL.ObjectProperty))
    g.add((MYONT.isDepartmentOf, RDFS.label, Literal("is department of")))
    g.add((MYONT.isDepartmentOf, RDFS.domain, MYONT.Department))
    g.add((MYONT.isDepartmentOf, RDFS.range, MYONT.Museum))

    ###############################################################################

    ############################ CUSTOM PROPERTIES ####################################

    g.add((MYONT.hasTheme, RDF.type, OWL.ObjectProperty))
    g.add((MYONT.hasTheme, RDFS.label, Literal("Theme")))
    g.add((MYONT.hasTheme, RDFS.domain, CRM.E22_Human_Made_Object))
    g.add((MYONT.hasTheme, RDFS.range, MYONT.Theme))

    g.add((MYONT.isThemeOf, RDF.type, OWL.ObjectProperty))
    g.add((MYONT.isThemeOf, RDFS.label, Literal("is theme of")))
    g.add((MYONT.isThemeOf, RDFS.domain, MYONT.Theme))
    g.add((MYONT.isThemeOf, RDFS.range, CRM.E22_Human_Made_Object))
    g.add((MYONT.hasTheme, OWL.inverseOf, MYONT.isThemeOf))

    g.add((MYONT.createdBy, RDF.type, OWL.ObjectProperty))
    g.add((MYONT.createdBy, RDFS.label, Literal("created by artist")))
    g.add((MYONT.createdBy, RDFS.domain, CRM.E22_Human_Made_Object))
    g.add((MYONT.createdBy, RDFS.range, MYONT.Artist))
    g.add((MYONT.createdBy, RDFS.subPropertyOf, CRM.P108i_was_produced_by))
    # g.add((MYONT.createdBy, RDFS.subPropertyOf, CRM.P14_carried_out_by))
    g.add((MYONT.createdBy, RDFS.subPropertyOf, SCHEMA.creator))
    g.add((MYONT.createdBy, OWL.inverseOf, MYONT.hasCreated))

    g.add((MYONT.displayedInDepartment, RDF.type, OWL.ObjectProperty))
    g.add((MYONT.displayedInDepartment, RDFS.label,
          Literal("displayed in department")))
    g.add((MYONT.displayedInDepartment, RDFS.domain, CRM.E22_Human_Made_Object))
    g.add((MYONT.displayedInDepartment, RDFS.range, MYONT.Department))
    # g.add((MYONT.displayedInDepartment, OWL.inverseOf, MYONT.displays))

    g.add((MYONT.displayedBy, RDF.type, OWL.ObjectProperty))
    g.add((MYONT.displayedBy, RDFS.label, Literal("displayed by museum")))
    g.add((MYONT.displayedBy, RDFS.domain, CRM.E22_Human_Made_Object))
    g.add((MYONT.displayedBy, RDFS.range, MYONT.Museum))
    g.add((MYONT.displayedBy, OWL.inverseOf, MYONT.displays))

    g.add((MYONT.displays, RDF.type, OWL.ObjectProperty))
    g.add((MYONT.displays, RDFS.label, Literal("displays")))
    g.add((MYONT.displays, RDFS.domain, MYONT.Museum))
    g.add((MYONT.displays, RDFS.range, CRM.E22_Human_Made_Object))

    g.add((MYONT.departmentDisplays, RDF.type, OWL.ObjectProperty))
    g.add((MYONT.departmentDisplays, RDFS.label, Literal("department displays")))
    g.add((MYONT.departmentDisplays, RDFS.domain, MYONT.Department))
    g.add((MYONT.departmentDisplays, RDFS.range, CRM.E22_Human_Made_Object))
    g.add((MYONT.departmentDisplays, OWL.inverseOf, MYONT.displayedInDepartment))

    g.add((MYONT.hasCreated, RDF.type, OWL.ObjectProperty))
    g.add((MYONT.hasCreated, RDFS.label, Literal("has created")))
    g.add((MYONT.hasCreated, RDFS.domain, MYONT.Artist))
    g.add((MYONT.hasCreated, RDFS.range, CRM.E22_Human_Made_Object))

    # remove if unstructured text source also doesn't populate it
    # g.add((MYONT.discoveredIn, RDF.type, OWL.ObjectProperty))
    # g.add((MYONT.discoveredIn, RDFS.label, Literal("discovered in")))
    # g.add((MYONT.discoveredIn, RDFS.domain, MYONT.Artifact))
    # g.add((MYONT.discoveredIn, RDFS.range, CRM.E53_Place))

    # ------------------------------- data properties---------------------------------

    g.add((MYONT.startDate, RDF.type, OWL.DatatypeProperty))
    g.add((MYONT.startDate, RDFS.label, Literal("started in")))
    g.add((MYONT.startDate, RDFS.domain, CRM.E22_Human_Made_Object))
    g.add((MYONT.startDate, RDFS.range, XSD.gYear))

    g.add((MYONT.endDate, RDF.type, OWL.DatatypeProperty))
    g.add((MYONT.endDate, RDFS.label, Literal("artwork finished in")))
    g.add((MYONT.endDate, RDFS.domain, CRM.E22_Human_Made_Object))
    g.add((MYONT.endDate, RDFS.range, XSD.gYear))

    g.add((MYONT.hasCulture, RDF.type, OWL.DatatypeProperty))
    g.add((MYONT.hasCulture, RDFS.label, Literal("culture")))
    g.add((MYONT.hasCulture, RDFS.domain, CRM.E22_Human_Made_Object))
    g.add((MYONT.hasCulture, RDFS.range, XSD.string))

    g.add((MYONT.mediumDescription, RDF.type, OWL.DatatypeProperty))
    g.add((MYONT.mediumDescription, RDFS.label, Literal("Labeled Medium")))
    g.add((MYONT.mediumDescription, RDFS.domain, CRM.E22_Human_Made_Object))
    g.add((MYONT.mediumDescription, RDFS.range, XSD.string))

    g.add((MYONT.hasNationality, RDF.type, OWL.DatatypeProperty))
    g.add((MYONT.hasNationality, RDFS.label, Literal("nationality")))
    g.add((MYONT.hasNationality, RDFS.domain, CRM.E21_Person))
    g.add((MYONT.hasNationality, RDFS.range, XSD.string))

    g.add((MYONT.hasPeriod, RDF.type, OWL.DatatypeProperty))
    g.add((MYONT.hasPeriod, RDFS.label, Literal("period")))
    g.add((MYONT.hasPeriod, RDFS.domain, CRM.E22_Human_Made_Object))
    g.add((MYONT.hasPeriod, RDFS.range, XSD.string))

    g.add((MYONT.hasObjectId, RDF.type, OWL.DatatypeProperty))
    # g.add((MYONT.hasObjectId, RDF.type, OWL.FunctionalProperty)) # issue could be different museums might have overlapping ones, solution: add museum name ahead of id
    g.add((MYONT.hasObjectId, RDFS.label, Literal("object id")))
    g.add((MYONT.hasObjectId, RDFS.domain, CRM.E22_Human_Made_Object))
    g.add((MYONT.hasObjectId, RDFS.range, XSD.integer))

    g.add((MYONT.hasDepartmentId, RDF.type, OWL.DatatypeProperty))
    g.add((MYONT.hasDepartmentId, RDFS.label, Literal("department id")))
    g.add((MYONT.hasDepartmentId, RDFS.domain, MYONT.Department))
    g.add((MYONT.hasDepartmentId, RDFS.range, XSD.integer))

    g.add((MYONT.bornOn, RDF.type, OWL.DatatypeProperty))
    g.add((MYONT.bornOn, RDFS.label, Literal("born in")))
    g.add((MYONT.bornOn, RDFS.domain, CRM.E21_Person))
    g.add((MYONT.bornOn, RDFS.range, XSD.gYear))

    g.add((MYONT.diedOn, RDF.type, OWL.DatatypeProperty))
    g.add((MYONT.diedOn, RDFS.label, Literal("died in")))
    g.add((MYONT.diedOn, RDFS.domain, CRM.E21_Person))
    g.add((MYONT.diedOn, RDFS.range, XSD.gYear))

    g.serialize(destination="my_ontology1.ttl", format="turtle")


g = Graph()
build_ontology(g)
