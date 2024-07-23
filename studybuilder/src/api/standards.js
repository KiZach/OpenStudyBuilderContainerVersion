import repository from './repository'

const resource = 'standards'

export default {
  getAllModels(params) {
    return repository.get(`${resource}/data-models`, { params })
  },
  getModelByUid(uid) {
    return repository.get(`${resource}/data-models/${uid}`)
  },
  getDatasetClasses(params) {
    return repository.get(`${resource}/dataset-classes`, { params })
  },
  getClassVariables(params) {
    return repository.get(`${resource}/class-variables`, { params })
  },
  getAllGuides(params) {
    return repository.get(`${resource}/data-model-igs`, { params })
  },
  getDatasets(params) {
    return repository.get(`${resource}/datasets`, { params })
  },
  getDatasetVariables(params) {
    return repository.get(`${resource}/dataset-variables`, { params })
  },
}
