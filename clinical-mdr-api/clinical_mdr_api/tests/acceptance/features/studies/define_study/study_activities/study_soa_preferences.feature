@REQ_ID:1074260
Feature: Manage and Maintain Study SOA preferences functionality in Clinical MDR API

# All the scenarios in this Gherkin specification, with flowchart (SoA), will include testing Protocal SoA, Detailed SoA and Operational SoA. 

    Background: Test user must be able to call the Clinical MDR API and test data exist
        Given The test user can call the Clinical MDR API
        Given A test study identified by 'uid' is available holding test data

    Scenario Outline: User must be able to request for the flowchart (SoA) with preferred time unit as day
        When The user requests for the flowchart (SoA) with preferred time unit as day
        Then The user receives the flowchart with study day view

            Test Coverage:
            |TestFile                                                        | TestID                               |
            |/tests/integration/api/service/test_study_flowchart.py | @TestID:test_get_flowchart_table              |
            |/tests/integration/api/study_selections/test_study_flowchart.py | @TestID:test_flowchart               |
            |/tests/integration/api/study_selections/test_study_flowchart.py | @TestID:test_flowchart_docx          |
            |/tests/integration/api/study_selections/test_study_flowchart.py | @TestID:test_flowchart_html          |

    Scenario Outline: User must be able to request for the flowchart (SoA) with preferred time unit as week
        When The user requests for the flowchart (SoA) with preferred time unit as week
        Then The user receives the flowchart with study week view

            Test Coverage:
            |TestFile                                                        | TestID                               |
            |/tests/integration/api/service/test_study_flowchart.py | @TestID:test_get_flowchart_table              |
            |/tests/integration/api/study_selections/test_study_flowchart.py | @TestID:test_flowchart               |
            |/tests/integration/api/study_selections/test_study_flowchart.py | @TestID:test_flowchart_docx          |
            |/tests/integration/api/study_selections/test_study_flowchart.py | @TestID:test_flowchart_html          | 

    #The following scenaio was tested manually in the current release, and the test scripts will be implemented in the later release
    @manual_test
    Scenario Outline: User must be able to request for the flowchart (SoA) with "baseline shown as time 0"
        When The user requests for the flowchart (SoA) with "Baseline shown as time 0"
        Then The user receives the flowchart with "study baseline shown as time 0" view