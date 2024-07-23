import { defineStore } from 'pinia'
import { inject } from 'vue'

import { i18n } from '@/plugins/i18n'
import generalUtils from '@/utils/generalUtils'
import { useStudiesGeneralStore } from './studies-general'

function getStudyUid() {
  const studyUidFromUrl = generalUtils.extractStudyUidFromUrl(
    document.location.pathname
  )
  if (studyUidFromUrl) {
    return studyUidFromUrl
  }
  const selectedStudyFromLocalStorage = JSON.parse(
    localStorage.getItem('selectedStudy')
  )
  if (selectedStudyFromLocalStorage) {
    return selectedStudyFromLocalStorage.uid
  }
  return '*'
}

const studyId = getStudyUid()

export const useAppStore = defineStore('app', {
  state: () => ({
    drawer: true,
    section: '',
    breadcrumbs: [],
    helpPath: '',
    userData: {},
    studyUid: 'none',
    menuItems: {
      Library: {
        url: '/library',
        items: [
          {
            title: i18n.t('Sidebar.library.about'),
            url: { name: 'LibrarySummary' },
            icon: 'mdi-information-outline',
          },
          {
            id: 'process_overview_tile',
            title: i18n.t('Sidebar.library.process_overview'),
            icon: 'mdi-arrow-right-bold-outline',
            url: { name: 'ProcessOverview' },
            description: i18n.t('Library.process_overview_description'),
          },
          {
            id: 'codelists_tile',
            title: i18n.t('Sidebar.library.code_lists'),
            icon: 'mdi-folder-text-outline',
            description: i18n.t('Library.codelist_description'),
            children: [
              {
                title: i18n.t('Sidebar.dashboard'),
                url: { name: 'CTDashboard' },
              },
              {
                title: i18n.t('Sidebar.library.ct_catalogues'),
                url: { name: 'CtCatalogues' },
              },
              {
                title: i18n.t('Sidebar.library.ct_packages'),
                url: { name: 'CtPackages' },
              },
              {
                title: i18n.t('Sidebar.library.cdisc'),
                url: { name: 'CDISC' },
              },
              {
                title: i18n.t('Sidebar.library.sponsor'),
                url: { name: 'Sponsor' },
              },
              {
                title: i18n.t('Sidebar.library.sponsor_ct_packages'),
                url: { name: 'SponsorCtPackages' },
              },
            ],
          },
          {
            id: 'dictionaries_tile',
            title: i18n.t('Sidebar.library.dictionaries'),
            icon: 'mdi-book-open-outline',
            description: i18n.t('Library.dictionaries_description'),
            children: [
              {
                title: i18n.t('Sidebar.library.snomed'),
                url: { name: 'Snomed' },
              },
              {
                title: i18n.t('Sidebar.library.meddra'),
                url: { name: 'MedDra' },
              },
              {
                title: i18n.t('Sidebar.library.medrt'),
                url: { name: 'MedRt' },
              },
              {
                title: i18n.t('Sidebar.library.unii'),
                url: { name: 'Unii' },
              },
              {
                title: i18n.t('Sidebar.library.loinc'),
                url: { name: 'Loinc' },
              },
              {
                title: i18n.t('Sidebar.library.ucum'),
                url: { name: 'Ucum' },
              },
            ],
          },
          {
            id: 'concepts_tile',
            title: i18n.t('Sidebar.library.concepts'),
            icon: 'mdi-car-shift-pattern',
            description: i18n.t('Library.concepts_description'),
            children: [
              {
                title: i18n.t('Sidebar.library.activities'),
                url: { name: 'Activities' },
              },
              {
                title: i18n.t('Sidebar.library.units'),
                url: { name: 'Units' },
              },
              {
                title: i18n.t('Sidebar.library.crfs'),
                url: { name: 'Crfs' },
              },
              // Temporarily removed
              // {
              //   title: i18n.t('Sidebar.library.compounds'),
              //   url: { name: 'Compounds' },
              // },
            ],
          },
          {
            id: 'syntax_templates_tile',
            title: i18n.t('Sidebar.library.syntax_templates'),
            icon: 'mdi-folder-star-outline',
            description: i18n.t('Library.syntax_templates_description'),
            children: [
              {
                title: i18n.t('Sidebar.library.objectives'),
                url: { name: 'ObjectiveTemplates' },
              },
              {
                title: i18n.t('Sidebar.library.endpoints'),
                url: { name: 'EndpointTemplates' },
              },
              {
                title: i18n.t('Sidebar.library.timeframes'),
                url: { name: 'TimeframeTemplates' },
              },
              {
                title: i18n.t('Sidebar.library.criteria'),
                url: { name: 'CriteriaTemplates' },
              },
              {
                title: i18n.t('Sidebar.library.activity_instructions'),
                url: { name: 'ActivityTemplates' },
              },
              {
                title: i18n.t('Sidebar.library.footnotes'),
                url: { name: 'FootnoteTemplates' },
              },
            ],
          },
          {
            id: 'template_instantiations_tile',
            title: i18n.t('Sidebar.library.template_instantiations'),
            icon: 'mdi-folder-account-outline',
            description: i18n.t('Library.template_instantiations_description'),
            children: [
              {
                title: i18n.t('Sidebar.library.objectives'),
                url: { name: 'Objectives' },
              },
              {
                title: i18n.t('Sidebar.library.endpoints'),
                url: { name: 'Endpoints' },
              },
              {
                title: i18n.t('Sidebar.library.timeframes'),
                url: { name: 'Timeframes' },
              },
              {
                title: i18n.t('Sidebar.library.criteria'),
                url: { name: 'CriteriaInstances' },
              },
              {
                title: i18n.t('Sidebar.library.activity_instructions'),
                url: { name: 'ActivityInstructions' },
              },
              {
                title: i18n.t('Sidebar.library.footnotes'),
                url: { name: 'FootnoteInstances' },
              },
            ],
          },
          {
            id: 'template_collections_tile',
            title: i18n.t('Sidebar.library.template_collections'),
            icon: 'mdi-folder-star-multiple-outline',
            description: i18n.t('Library.template_collections_description'),
            children: [
              {
                title: i18n.t('Sidebar.library.project_templates'),
                url: { name: 'ProjectTemplates' },
              },
              {
                title: i18n.t('Sidebar.library.shared_templates'),
                url: { name: 'SharedTemplates' },
              },
              {
                title: i18n.t('Sidebar.library.supporting_templates'),
                url: { name: 'SupportingTemplates' },
              },
            ],
          },
          {
            id: 'data_exchange_std_tile',
            title: i18n.t('Sidebar.library.data_exchange_std'),
            icon: 'mdi-arrow-decision-outline',
            description: i18n.t('Library.data_exchange_standards_description'),
            children: [
              {
                title: i18n.t('Sidebar.library.cdash'),
                url: { name: 'Cdash' },
              },
              {
                title: i18n.t('Sidebar.library.sdtm'),
                url: { name: 'Sdtm' },
              },
              {
                title: i18n.t('Sidebar.library.adam'),
                url: { name: 'Adam' },
              },
            ],
          },
          {
            id: 'admin_defs_tile',
            title: i18n.t('Sidebar.library.administrative_definitions'),
            icon: 'mdi-police-badge-outline',
            description: i18n.t('Library.administrative_definitions'),
            children: [
              {
                id: 'clinical_programmes',
                title: i18n.t('Sidebar.library.clinical_programmes'),
                icon: 'mdi-archive-outline',
                url: { name: 'ClinicalProgrammes' },
                description: i18n.t('Library.clinical_programmes'),
              },
              {
                id: 'projects',
                title: i18n.t('Sidebar.library.projects'),
                icon: 'mdi-clipboard-outline',
                url: { name: 'Projects' },
                description: i18n.t('Library.projects'),
              },
            ],
          },
          {
            id: 'list_tile',
            title: i18n.t('Sidebar.library.list'),
            icon: 'mdi-format-list-bulleted-square',
            description: i18n.t('Library.list_description'),
            children: [
              {
                title: i18n.t('Sidebar.library.cdash_std'),
                url: { name: 'CdashStandards' },
              },
              {
                title: i18n.t('Sidebar.library.sdtm_std_cst'),
                url: { name: 'SdtmStdCst' },
              },
              {
                title: i18n.t('Sidebar.library.sdtm_std_dmw'),
                url: { name: 'SdtmStdDmw' },
              },
              {
                title: i18n.t('Sidebar.library.adam_std_cst'),
                url: { name: 'AdamStdCst' },
              },
              {
                title: i18n.t('Sidebar.library.adam_std_new'),
                url: { name: 'AdamStdNew' },
              },
            ],
          },
        ],
      },
      Studies: {
        url: '/study',
        items: [
          {
            title: i18n.t('Sidebar.study.about'),
            url: { name: 'StudySummary' },
            icon: 'mdi-information-outline',
          },
          {
            id: 'process_overview_tile',
            title: i18n.t('Sidebar.study.process_overview'),
            icon: 'mdi-arrow-right-bold-outline',
            children: [
              {
                title: i18n.t('Sidebar.study.protocol_process'),
                url: { name: 'ProtocolProcess' },
              },
            ],
            description: i18n.t('Studies.process_overview_description'),
          },
          {
            title: i18n.t('Sidebar.study.select'),
            url: { name: 'SelectOrAddStudy' },
            description: i18n.t('Studies.list_description'),
            icon: 'mdi-view-list',
          },
          {
            title: i18n.t('Sidebar.study.manage'),
            icon: 'mdi-wrench-outline',
            description: i18n.t('Studies.manage_description'),
            children: [
              {
                title: i18n.t('Sidebar.study.study_status'),
                url: { name: 'StudyStatus', params: { study_id: studyId } },
                studyRequired: true,
              },
            ],
          },
          {
            title: i18n.t('Sidebar.study.define'),
            icon: 'mdi-note-edit-outline',
            description: i18n.t('Studies.define_description'),
            children: [
              // {
              //   title: i18n.t('Sidebar.study.specification_overview'),
              //   url: { name: 'SpecificationDashboard', params: { study_id: studyId } },
              //   studyRequired: true,
              //   hidden: true
              // },
              {
                title: i18n.t('Sidebar.study.study_title'),
                url: { name: 'StudyTitle', params: { study_id: studyId } },
                studyRequired: true,
              },
              {
                title: i18n.t('Sidebar.study.registry_ids'),
                url: {
                  name: 'StudyRegistryIdentifiers',
                  params: { study_id: studyId },
                },
                studyRequired: true,
              },
              {
                title: i18n.t('Sidebar.study.study_properties'),
                url: { name: 'StudyProperties', params: { study_id: studyId } },
                studyRequired: true,
              },
              {
                title: i18n.t('Sidebar.study.study_structure'),
                url: { name: 'StudyStructure', params: { study_id: studyId } },
                studyRequired: true,
              },
              {
                title: i18n.t('Sidebar.study.population'),
                url: { name: 'StudyPopulation', params: { study_id: studyId } },
                studyRequired: true,
              },
              {
                title: i18n.t('Sidebar.study.study_criteria'),
                url: {
                  name: 'StudySelectionCriteria',
                  params: { study_id: studyId },
                },
                studyRequired: true,
              },
              // Temporarily removed
              // {
              //   title: i18n.t('Sidebar.study.study_interventions'),
              //   url: {
              //     name: 'StudyInterventions',
              //     params: { study_id: studyId },
              //   },
              //   studyRequired: true,
              // },
              {
                title: i18n.t('Sidebar.study.purpose'),
                url: { name: 'StudyPurpose', params: { study_id: studyId } },
                studyRequired: true,
              },
              {
                title: i18n.t('Sidebar.study.activities'),
                url: { name: 'StudyActivities', params: { study_id: studyId } },
                studyRequired: true,
              },
              {
                title: i18n.t('Sidebar.study.data_specifications'),
                url: {
                  name: 'StudyDataSpecifications',
                  params: { study_id: studyId },
                },
                studyRequired: true,
              },
              // {
              //   title: i18n.t('Sidebar.study.terminology'),
              //   url: { name: 'StudyTerminology', params: { study_id: studyId } },
              //   hidden: true
              // }
            ],
          },
          {
            title: i18n.t('Sidebar.study.build'),
            icon: 'mdi-apps',
            description: i18n.t('Studies.build_description'),
            children: [
              // {
              //   title: i18n.t('Sidebar.study.standarisation_plan'),
              //   url: { name: 'StandardisationPlan' },
              //   hidden: true
              // },
              {
                title: i18n.t('Sidebar.study.protocol_elements'),
                url: {
                  name: 'ProtocolElements',
                  params: { study_id: studyId },
                },
                studyRequired: true,
              },
              // {
              //   title: i18n.t('Sidebar.study.crf_specifications'),
              //   url: { name: 'CrfSpecifications' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.study_disclosure'),
              //   url: { name: 'StudyDisclosure' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.trial_supplies_spec'),
              //   url: { name: 'TrialSuppliesSpecifications' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.odm_specification'),
              //   url: { name: 'OdmSpecification' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.ctr_odm_xml'),
              //   url: { name: 'CtrOdmXml' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.sdtm_specification'),
              //   url: { name: 'SdtmSpecification' },
              //   hidden: true
              // },
              {
                title: i18n.t('Sidebar.study.sdtm_study'),
                url: {
                  name: 'SdtmStudyDesignDatasets',
                  params: { study_id: studyId },
                },
                studyRequired: true,
              },
              // {
              //   title: i18n.t('Sidebar.study.adam_spec'),
              //   url: { name: 'AdamSpecification' },
              //   hidden: true
              // }
            ],
          },
          {
            title: i18n.t('Sidebar.study.list'),
            icon: 'mdi-format-list-bulleted-square',
            description: i18n.t('Studies.list_description'),
            children: [
              // {
              //   title: i18n.t('Sidebar.study.mma_trial_metadata'),
              //   url: { name: 'MmaTrialMetadata' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.sdtm_define_p21'),
              //   url: { name: 'SdtmDefineP21' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.sdtm_define_cst'),
              //   url: { name: 'SdtmDefineCst' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.dmw_additional_metadata'),
              //   url: { name: 'DmwAdditionalMetadata' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.sdtm_additional_metadata'),
              //   url: { name: 'SdtmAdditionalMetadata' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.adam_define_p21'),
              //   url: { name: 'AdamDefineP21' },
              //   hidden: true
              // },
              // {
              //   title: i18n.t('Sidebar.study.adam_define_cst'),
              //   url: { name: 'AdamDefineCst' },
              //   hidden: true
              // },
              {
                title: i18n.t('Sidebar.study.analysis_study_metadata_new'),
                url: {
                  name: 'AnalysisStudyMetadataNew',
                  params: { study_id: studyId },
                },
                studyRequired: true,
              },
            ],
          },
        ],
      },
      Admin: {},
      Help: {},
    },
  }),

  getters: {
    getBreadcrumbsLevel: (state) => (level) => {
      if (state.breadcrumbs.length > level) {
        return state.breadcrumbs[level]
      }
      return undefined
    },
    helpUrl: (state) => {
      const $config = inject('$config')
      const baseUrl = $config.DOC_BASE_URL.replace(/\/+$/, '')
      if (state.helpPath) {
        return `${baseUrl}/guides/${state.helpPath}`
      }
      return `${baseUrl}/guides/userguide/userguides_introduction.html`
    },
    libraryMenu: (state) => state.menuItems.Library,
    studiesMenu: (state) => state.menuItems.Studies,
    findMenuItemPath: (state) => (section, routeName) => {
      let result
      let subResult
      state.menuItems[section].items.forEach((item) => {
        if (item.url && item.url.name === routeName) {
          result = item
        } else if (item.children && item.children.length) {
          item.children.forEach((subItem) => {
            if (subItem.url.name === routeName) {
              result = item
              subResult = subItem
            }
          })
        }
      })
      return [result, subResult]
    },
  },

  actions: {
    setSection(section) {
      this.section = section
      localStorage.setItem('section', section)
      if (section) {
        this.breadcrumbs = [
          {
            title: section,
            disabled: true,
            to: { name: section },
            exact: true,
          },
        ]
      }
    },
    setBreadcrumbs(breadcrumbs) {
      this.breadcrumbs = breadcrumbs
    },
    initialize() {
      const studiesGeneralStore = useStudiesGeneralStore()
      const section = localStorage.getItem('section')
      const breadcrumbs = localStorage.getItem('breadcrumbs')
      const userData = localStorage.getItem('userData')

      if (section) {
        this.section = section
      }
      if (breadcrumbs) {
        this.breadcrumbs = JSON.parse(breadcrumbs)
      }
      if (userData) {
        this.userData = JSON.parse(userData)
      } else {
        this.userData = { darkTheme: false, rows: 10, studyNumberLength: 4 }
      }
      studiesGeneralStore.initialize()
    },
    appendToBreadcrumbs(item) {
      for (const level of this.breadcrumbs) {
        level.disabled = false
      }
      item.disabled = true
      this.breadcrumbs.push(item)
    },
    addBreadcrumbsLevel(title, to, index, replace) {
      const item = {
        title,
        to,
        exact: true,
      }
      const lastIndex = this.breadcrumbs.length - 1
      if (
        this.breadcrumbs.length &&
        index === lastIndex &&
        this.breadcrumbs[lastIndex].title === item.title
      ) {
        return
      }
      if (index !== undefined) {
        if (!replace) {
          this.breadcrumbs = this.breadcrumbs.slice(0, index)
          this.appendToBreadcrumbs(item)
        } else {
          item.disabled = index === this.breadcrumbs.length - 1
          this.breadcrumbs[index] = item
          this.breadcrumbs = this.breadcrumbs.slice(0, index + 1)
        }
      } else {
        this.appendToBreadcrumbs(item)
      }
      localStorage.setItem('breadcrumbs', JSON.stringify(this.breadcrumbs))
    },
    truncateBreadcrumbsFromLevel(pos) {
      this.breadcrumbs = this.breadcrumbs.slice(0, pos)
      localStorage.setItem('breadcrumbs', JSON.stringify(this.breadcrumbs))
    },
    resetBreadcrumbs() {
      this.breadcrumbs = []
      localStorage.removeItem('section')
      localStorage.removeItem('breadcrumbs')
    },
    saveUserData(data) {
      this.userData = data
      localStorage.setItem('userData', JSON.stringify(data))
    },
  },
})
