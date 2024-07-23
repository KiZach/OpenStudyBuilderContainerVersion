import repository from './repository'

const resource = 'clinical-programmes'

export default {
  get(options) {
    const params = {
      ...options,
    }
    return repository.get(resource, { params })
  },
  create(data) {
    const params = {
      ...data,
    }
    return repository.post(resource, params)
  },
}
