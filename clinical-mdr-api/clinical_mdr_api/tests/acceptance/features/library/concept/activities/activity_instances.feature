@REQ_ID:1975905

Feature: Gherkin API specification for Activity Instances

    I want to be able to create activity instance when relevant information is provided

    Scenario: Create activity instance when all relevant data is provided
        Given The activity was already created
        And The library name is provided
        And The Activity Group uid is provided 
        And The Activity Subgroup uid is provided
        And The Activity Instance Class uid is provided
        Then The Activity Instance is created successfully

    
    Scenario: The activity instance must not be created when activity is not provided
        Given The activity was not already created
        And The library name is provided
        And The Activity Group uid is provided 
        And The Activity Subgroup uid is provided
        And The Activity Instance Class uid is provided
        Then The Activity Instance is not created successfully

    Scenario: The activity instance must not be created when activity group is not provided
        Given The activity was already created
        And The library name is provided
        And The Activity Group uid is not provided 
        And The Activity Subgroup uid is provided
        And The Activity Instance Class uid is provided
        Then The Activity Instance is not created successfully

    Scenario: The activity instance must not be created when activity subgroup is not provided
        Given The activity was already created
        And The library name is provided
        And The Activity Group uid is provided 
        And The Activity Subgroup uid is not provided
        And The Activity Instance Class uid is provided
        Then The Activity Instance is not created successfully     

    Scenario: The activity instance must not be created when Activity Instance Class is not provided
        Given The activity was already created
        And The library name is provided
        And The Activity Group uid is provided 
        And The Activity Subgroup uid is not provided
        And The Activity Instance Class uid is not provided
        Then The Activity Instance is not created successfully      
     
    Scenario: An activity instance with the same name must not be created more than once
        Given The activity was already created
        And Complete activity instance definition is provided
        And Same name for activity instance was provided as an existing one
        Then API refuses the request

    Scenario: An activity instance  must not be created when there is uid mismatch
        Given The activity was already created
        And The Activity group uid is provided for Activity subgroup uid
        And The activity subgroup uid is provided for activity group uid
        Then API refuses the request

    Scenario: An activity instance must not be created when activity group and activity subgroup combination does not existing
        Given The activity was already created
        And The activity group uid is provided
        And The activity subgroup uid is provided
        And The activity group uid and activity subgroup uid are not in valid combination
        Then API refuses the request

    Scenario: An activity instance must not be created when both standard unit and categorical response list are provided
        Given The activity was already created
        And Complete activity instance definition is provided
        And Unit dimension and Standard Unit are provided
        And Categorical response list is provided
        Then API refuses the request

    Scenario: An activity instance created as numeric finding activity instance class must have unit dimension and standard unit
        Given The activity was already created
        And A valid activity group and activity subgroup combination was provided
        And Unit dimension and standard unit are provided
        Then The activity instance is created successfully

    Scenario: An activity instance created as numeric finding activity instance class must not have unit dimension and standard unit empty
        Given The activity was already created
        And A valid activity group and activity subgroup combination was provided
        And Unit dimension and standard unit are not provided
        Then API refuses the request

    Scenario: An activity instance created as categoric finding activity instance class must have categorical response list
        Given The activity was already created
        And A valid activity group and activity subgroup combination was provided
        And Categorical response list is provided
        Then The activity instance is created successfully                

    Scenario: An activity instance created as categoric finding activity instance class must not have categorical response list empty
        Given The activity was already created
        And A valid activity group and activity subgroup combination was provided
        And Categorical response list is not provided
        Then API refuses the request