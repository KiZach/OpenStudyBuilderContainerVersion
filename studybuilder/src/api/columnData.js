import repository from './repository'

export default {
  getHeaderData(options, resource) {
    const params = {
      ...options,
    }
    return repository.get(`${resource}/headers`, { params })
  },
}
