import repository from './repository'

const resource = 'dictionaries'

export default {
  getCodelists(library) {
    return repository.get(`${resource}/codelists`, {
      params: { library: library, page_size: 0 },
    })
  },
  getTerms(options) {
    const params = {
      ...options,
    }
    return repository.get(`${resource}/terms`, { params })
  },
  getSubstances(params) {
    return repository.get(`${resource}/substances`, { params })
  },
  inactivate(uid) {
    return repository.delete(`${resource}/terms/${uid}/activations`)
  },
  reactivate(uid) {
    return repository.post(`${resource}/terms/${uid}/activations`)
  },
  delete(uid) {
    return repository.delete(`${resource}/terms/${uid}`)
  },
  approve(uid) {
    return repository.post(`${resource}/terms/${uid}/approvals`)
  },
  newVersion(uid) {
    return repository.post(`${resource}/terms/${uid}/versions`)
  },
  edit(uid, term) {
    const params = {
      ...term,
    }
    return repository.patch(`${resource}/terms/${uid}`, params)
  },
  create(term) {
    const params = {
      ...term,
    }
    return repository.post(`${resource}/terms`, params)
  },
}
