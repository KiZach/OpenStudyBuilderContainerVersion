import repository from './repository'

const resource = 'activity-instance-classes'

export default {
  getAll(params) {
    return repository.get(resource, { params })
  },
}
