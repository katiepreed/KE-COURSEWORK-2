from rdflib import Namespace, Literal
from rdflib.namespace import RDF, RDFS, OWL, XSD

MYONT = Namespace("https://ontologeez/")
SCHEMA = Namespace("https://schema.org/")
CRM    = Namespace("http://www.cidoc-crm.org/cidoc-crm/")

def build_ontology(g):
    g.bind("myont", MYONT)
    g.bind("schema", SCHEMA)
    g.bind("crm", CRM)

    ############### CIDOC CLASSES #################################################

    # g.add((CRM.E1_CRM_Entity, RDF.type, OWL.Class))

    g.add((CRM.E22_Human_Made_Object, RDF.type, OWL.Class))
    g.add((CRM.E22_Human_Made_Object, RDFS.label, Literal("Human Made Object")))

    # g.add((CRM.E52_Time-Span, RDF.type, OWL.Class))
    # g.add((CRM.E52_Time-Span, RDFS.label, Literal("Time span")))

    g.add((CRM.E39_Actor, RDF.type, OWL.Class))
    g.add((CRM.E39_Actor, RDFS.label, Literal("Actor")))

    g.add((CRM.E21_Person, RDF.type, OWL.Class))
    g.add((CRM.E21_Person, RDFS.label, Literal("Person")))
    g.add((CRM.E21_Person, RDFS.subClassOf, CRM.E39_Actor))

    g.add((CRM.E53_Place, RDF.type, OWL.Class))
    g.add((CRM.E53_Place, RDFS.label, Literal("Place")))

    ###############################################################################

    ############################ SCHEMA CLASSES ####################################

    # g.add((SCHEMA.Thing, RDF.type, OWL.Class))

    g.add((SCHEMA.Painting, RDF.type, OWL.Class))
    g.add((SCHEMA.Painting, RDFS.label, Literal("Painting")))
    # g.add((SCHEMA.Painting, RDFS.subClassOf, CRM.E22_Human_Made_Object))

    g.add((SCHEMA.Sculpture, RDF.type, OWL.Class))
    g.add((SCHEMA.Sculpture, RDFS.label, Literal("Sculpture"))) # with known artist
    # g.add((SCHEMA.Sculpture, RDFS.subClassOf, CRM.E22_Human_Made_Object))
    # g.add((SCHEMA.Sculpture, RDFS.comment, Literal("Any sculpture that has a known artist is included here.")))

    g.add((SCHEMA.Museum, RDF.type, OWL.Class))
    g.add((SCHEMA.Museum, RDFS.label, Literal("Museum")))

    # only one equivalence statement is necessary
    g.add((SCHEMA.Person, RDF.type, OWL.Class))
    g.add((SCHEMA.Person, RDFS.label, Literal("Person")))
    g.add((SCHEMA.Person, OWL.equivalentClass, CRM.E21_Person))

    ################################################################################

    ################################ Custom Classes ###############################

    g.add((MYONT.Painting, RDF.type, OWL.Class))
    g.add((MYONT.Painting, RDFS.subClassOf, CRM.E22_Human_Made_Object))
    g.add((MYONT.Painting, RDFS.label, Literal("Painting")))
    g.add((MYONT.Painting, OWL.equivalentClass, SCHEMA.Painting))

    g.add((MYONT.Sculpture, RDF.type, OWL.Class))
    g.add((MYONT.Sculpture, RDFS.subClassOf, CRM.E22_Human_Made_Object))
    g.add((MYONT.Sculpture, RDFS.label, Literal("Sculpture")))
    g.add((MYONT.Sculpture, OWL.equivalentClass, SCHEMA.Sculpture))

    g.add((MYONT.Artist, RDF.type, OWL.Class))
    g.add((MYONT.Artist, RDFS.label, Literal("Artist")))
    g.add((MYONT.Artist, RDFS.subClassOf, CRM.E21_Person))
    # g.add((MYONT.Artist, RDFS.subClassOf, SCHEMA.Person))
    
    g.add((MYONT.Museum, RDF.type, OWL.Class))
    g.add((MYONT.Museum, RDFS.label, Literal("Museum")))
    g.add((MYONT.Museum, OWL.equivalentClass, SCHEMA.Museum))

    g.add((MYONT.Artifact, RDF.type, OWL.Class))
    g.add((MYONT.Artifact, RDFS.label, Literal("Artifact"))) # when artist is not known - the thing is more discovered
    g.add((MYONT.Artifact, RDFS.subClassOf, CRM.E22_Human_Made_Object))

    g.add((MYONT.Vase, RDF.type, OWL.Class))
    g.add((MYONT.Vase, RDFS.label, Literal("Vase")))
    g.add((MYONT.Vase, RDFS.subClassOf, MYONT.Artifact))

    g.add((MYONT.Ceramic, RDF.type, OWL.Class))
    g.add((MYONT.Ceramic, RDFS.label, Literal("Ceramic")))
    g.add((MYONT.Ceramic, RDFS.subClassOf, MYONT.Artifact))

    g.add((MYONT.Jewellery, RDF.type, OWL.Class))
    g.add((MYONT.Jewellery, RDFS.label, Literal("Jewellery")))
    g.add((MYONT.Jewellery, RDFS.subClassOf, MYONT.Artifact))

    g.add((MYONT.Scroll, RDF.type, OWL.Class))
    g.add((MYONT.Scroll, RDFS.label, Literal("Scroll")))
    g.add((MYONT.Scroll, RDFS.subClassOf, MYONT.Artifact))

    g.add((MYONT.Statue, RDF.type, OWL.Class))
    g.add((MYONT.Statue, RDFS.label, Literal("Statue"))) 
    g.add((MYONT.Statue, RDFS.subClassOf, MYONT.Artifact))

    g.add((MYONT.Figurine, RDF.type, OWL.Class))
    g.add((MYONT.Figurine, RDFS.label, Literal("Figurine")))
    g.add((MYONT.Figurine, RDFS.subClassOf, MYONT.Artifact))

    g.add((MYONT.Theme, RDF.type, OWL.Class))
    g.add((MYONT.Theme, RDFS.label, Literal("Theme")))

    g.add((MYONT.NatureTheme, RDF.type, OWL.Class))
    g.add((MYONT.NatureTheme, RDFS.label, Literal("Nature theme")))
    g.add((MYONT.NatureTheme, RDFS.subClassOf, MYONT.Theme))

    g.add((MYONT.AnimalTheme, RDF.type, OWL.Class))
    g.add((MYONT.AnimalTheme, RDFS.label, Literal("Animal theme")))
    g.add((MYONT.AnimalTheme, RDFS.subClassOf, MYONT.Theme))

    g.add((MYONT.ReligiousTheme, RDF.type, OWL.Class))
    g.add((MYONT.ReligiousTheme, RDFS.label, Literal("Religious theme")))
    g.add((MYONT.ReligiousTheme, RDFS.subClassOf, MYONT.Theme))

    g.add((MYONT.MythologicalTheme, RDF.type, OWL.Class))
    g.add((MYONT.MythologicalTheme, RDFS.label, Literal("Mythological theme")))
    g.add((MYONT.MythologicalTheme, RDFS.subClassOf, MYONT.Theme))

    g.add((MYONT.Department, RDF.type, OWL.Class))
    g.add((MYONT.Department, RDFS.label, Literal("Department")))

    g.add((MYONT.City, RDF.type, OWL.Class))
    g.add((MYONT.City, RDFS.label, Literal("City")))
    g.add((MYONT.City, RDFS.subClassOf, CRM.E53_Place))

    g.add((MYONT.Region, RDF.type, OWL.Class))
    g.add((MYONT.Region, RDFS.label, Literal("Region")))
    g.add((MYONT.Region, RDFS.subClassOf, CRM.E53_Place))

    g.add((MYONT.Country, RDF.type, OWL.Class))
    g.add((MYONT.Country, RDFS.label, Literal("Country")))
    g.add((MYONT.Country, RDFS.subClassOf, CRM.E53_Place))


    ###############################################################################

    ############################ SCHEMA.ORG PROPERTIES ####################################

    g.add((SCHEMA.name, RDF.type, OWL.DatatypeProperty))
    g.add((SCHEMA.name, RDFS.range, XSD.string))
    # g.add((SCHEMA.name, OWL.equivalentProperty, CRM.P102_has_title))
    # g.add((SCHEMA.name, RDFS.subPropertyOf, CRM.P102_has_title))


    g.add((SCHEMA.dateCreated, RDF.type, OWL.DatatypeProperty))
    g.add((SCHEMA.dateCreated, RDFS.domain, CRM.E22_Human_Made_Object))
    g.add((SCHEMA.dateCreated, RDFS.range, XSD.string)) # use this format for dates in data preprocessing

    #--------------------------------------------------------------------------------

    g.add((SCHEMA.displayLocation, RDF.type, OWL.ObjectProperty))
    g.add((SCHEMA.displayLocation, RDFS.domain, CRM.E22_Human_Made_Object))
    g.add((SCHEMA.displayLocation, RDFS.range, CRM.E53_Place))
    g.add((SCHEMA.displayLocation, OWL.equivalentProperty, CRM.P55_has_current_location))

    g.add((SCHEMA.locationCreated, RDF.type, OWL.ObjectProperty))
    g.add((SCHEMA.locationCreated, RDFS.domain, CRM.E22_Human_Made_Object))
    g.add((SCHEMA.locationCreated, RDFS.range, CRM.E53_Place))
    # g.add((SCHEMA.locationCreated, RDFS.subPropertyOf, MYONT.createdIn))

    g.add((SCHEMA.creator, RDF.type, OWL.ObjectProperty))
    # g.add((SCHEMA.creator, RDFS.domain, CRM.E22_Human_Made_Object))
    # g.add((SCHEMA.creator, RDFS.range, MYONT.Artist))
    # g.add((SCHEMA.creator, OWL.inverseOf, MYONT.hasCreated))

    ###############################################################################

    ############################ CIDOC PROPERTIES ####################################

    g.add((CRM.P55_has_current_location, RDF.type, OWL.ObjectProperty))
    g.add((CRM.P55_has_current_location, RDFS.domain, CRM.E22_Human_Made_Object))
    g.add((CRM.P55_has_current_location, RDFS.range, CRM.E53_Place))

    g.add((CRM.P102_has_title, RDF.type, OWL.DatatypeProperty))
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
    g.add((CRM.P108i_was_produced_by, RDFS.domain, CRM.E22_Human_Made_Object))
    g.add((CRM.P108i_was_produced_by, RDFS.range, MYONT.Artist))

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
    g.add((MYONT.displayedInDepartment, RDFS.label, Literal("displayed in department")))
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

    g.add((MYONT.hasCreated, RDF.type, OWL.ObjectProperty))
    g.add((MYONT.hasCreated, RDFS.label, Literal("has created")))
    g.add((MYONT.hasCreated, RDFS.domain, MYONT.Artist))
    g.add((MYONT.hasCreated, RDFS.range, CRM.E22_Human_Made_Object))

    # remove if unstructured text source also doesn't populate it
    g.add((MYONT.discoveredIn, RDF.type, OWL.ObjectProperty))
    g.add((MYONT.discoveredIn, RDFS.label, Literal("discovered in")))
    g.add((MYONT.discoveredIn, RDFS.domain, MYONT.Artifact))
    g.add((MYONT.discoveredIn, RDFS.range, CRM.E53_Place))

    #------------------------------- data properties---------------------------------

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