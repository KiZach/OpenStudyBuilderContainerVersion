import { defineStore } from 'pinia'

import dictionaries from '@/api/dictionaries'
import study from '@/api/study'
import terms from '@/api/controlledTerminology/terms'
import units from '@/api/units'

export const useStudiesGeneralStore = defineStore('studiesGeneral', {
  state: () => ({
    selectedStudy: null,
    selectedStudyVersion: null,
    studyPreferredTimeUnit: null,
    soaPreferredTimeUnit: null,
    soaPreferences: null,
    studyTypes: [],
    trialIntentTypes: [],
    trialTypes: [],
    trialPhases: [],
    interventionTypes: [],
    snomedTerms: [],
    sexOfParticipants: [],
    trialBlindingSchemas: [],
    controlTypes: [],
    interventionModels: [],
    units: [],
    nullValues: [],
    objectiveLevels: [],
    endpointLevels: [],
    endpointSubLevels: [],
    allUnits: [],
  }),

  getters: {
    sortedObjectiveLevels: (state) => {
      return state.objectiveLevels.sort((a, b) => {
        return a.order - b.order
      })
    },
    sortedEndpointLevels: (state) => {
      return state.endpointLevels.sort((a, b) => {
        return a.order - b.order
      })
    },
    studyId: (state) => {
      const studyNumber =
        state.selectedStudy.current_metadata.identification_metadata
          .study_number
      return studyNumber !== undefined && studyNumber !== null
        ? state.selectedStudy.current_metadata.identification_metadata.study_id
        : state.selectedStudy.current_metadata.identification_metadata
            .study_acronym
    },
  },

  actions: {
    unselectStudy() {
      this.selectedStudy = null
      localStorage.removeItem('selectedStudy')
    },

    async initialize() {
      const selectedStudy = localStorage.getItem('selectedStudy')
      if (selectedStudy) {
        const parsedStudy = JSON.parse(selectedStudy)
        this.selectStudy(parsedStudy)
        try {
          await study.getStudy(parsedStudy.uid, true)
        } catch (error) {
          this.unselectStudy()
        }
      }
    },
    selectStudy(studyObj, forceReload) {
      this.selectedStudy = studyObj
      this.selectedStudyVersion =
        studyObj.current_metadata.version_metadata.version_number
      localStorage.setItem('selectedStudy', JSON.stringify(studyObj))
      if (forceReload) {
        document.location.reload()
      }
      study.getStudyPreferredTimeUnit(studyObj.uid).then((resp) => {
        this.studyPreferredTimeUnit = resp.data
      })
      study.getSoAPreferredTimeUnit(studyObj.uid).then((resp) => {
        this.soaPreferredTimeUnit = resp.data
      })
      study.getSoAPreferences(studyObj.uid).then((resp) => {
        this.soaPreferences = resp.data
      })
    },
    setStudyPreferredTimeUnit({ timeUnitUid, protocolSoa }) {
      const data = { unit_definition_uid: timeUnitUid }
      return study
        .updateStudyPreferredTimeUnit(this.selectedStudy.uid, data, protocolSoa)
        .then((resp) => {
          protocolSoa
            ? (this.soaPreferredTimeUnit = resp.data)
            : (this.studyPreferredTimeUnit = resp.data)
        })
    },
    setSoaPreferences({ show_epochs, show_milestones, baseline_as_time_zero }) {
      return study
        .updateSoaPreferences(this.selectedStudy.uid, {
          show_epochs,
          show_milestones,
          baseline_as_time_zero,
        })
        .then((resp) => {
          this.soaPreferences = resp.data
        })
    },
    fetchUnits() {
      units.getBySubset('Study Time').then((resp) => {
        this.units = resp.data.items
      })
    },
    fetchAllUnits() {
      units.get({ params: { page_size: 0 } }).then((resp) => {
        this.allUnits = resp.data.items
      })
    },
    fetchStudyTypes() {
      terms.getNamesByCodelist('studyType').then((resp) => {
        this.studyTypes = resp.data.items
      })
    },
    fetchTrialIntentTypes() {
      terms.getNamesByCodelist('trialIntentType').then((resp) => {
        this.trialIntentTypes = resp.data.items
      })
    },
    fetchTrialTypes() {
      terms.getNamesByCodelist('trialType').then((resp) => {
        this.trialTypes = resp.data.items
      })
    },
    fetchTrialPhases() {
      terms.getNamesByCodelist('trialPhase').then((resp) => {
        this.trialPhases = resp.data.items
      })
    },
    fetchInterventionTypes() {
      terms.getNamesByCodelist('interventionTypes').then((resp) => {
        this.interventionTypes = resp.data.items
      })
    },
    fetchSnomedTerms() {
      dictionaries.getCodelists('SNOMED').then((resp) => {
        const params = {
          codelist_uid: resp.data.items[0].codelist_uid,
          page_size: 0,
          sort_by: JSON.stringify({'name': true})
        }
        dictionaries.getTerms(params).then((resp) => {
          this.snomedTerms = resp.data.items
        })
      })
    },
    fetchSexOfParticipants() {
      terms.getNamesByCodelist('sexOfParticipants').then((resp) => {
        this.sexOfParticipants = resp.data.items
      })
    },
    fetchTrialBlindingSchemas() {
      terms.getNamesByCodelist('trialBlindingSchema').then((resp) => {
        this.trialBlindingSchemas = resp.data.items
      })
    },
    fetchControlTypes() {
      terms.getNamesByCodelist('controlType').then((resp) => {
        this.controlTypes = resp.data.items
      })
    },
    fetchInterventionModels() {
      terms.getNamesByCodelist('interventionModel').then((resp) => {
        this.interventionModels = resp.data.items
      })
    },
    fetchNullValues() {
      terms.getByCodelist('nullValues').then((resp) => {
        this.nullValues = resp.data.items
      })
    },
    fetchObjectiveLevels() {
      terms.getNamesByCodelist('objectiveLevels').then((resp) => {
        // FIXME: deal with pagination to retrieve all items
        this.objectiveLevels = resp.data.items
      })
    },
    fetchEndpointLevels() {
      terms.getNamesByCodelist('endpointLevels').then((resp) => {
        // FIXME: deal with pagination to retrieve all items
        this.endpointLevels = resp.data.items
      })
    },
    fetchEndpointSubLevels() {
      terms.getNamesByCodelist('endpointSubLevels').then((resp) => {
        // FIXME: deal with pagination to retrieve all items
        this.endpointSubLevels = resp.data.items
      })
    },
  },
})
