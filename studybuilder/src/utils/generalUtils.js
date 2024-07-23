function extractStudyUidFromUrl(path) {
  const studyUidMatch = path.match(/\/studies\/(Study_[0-9]+)/i)
  if (studyUidMatch) {
    return studyUidMatch[1]
  } else {
    return null
  }
}

function extractStudyUidFromLocalStorage() {
  const selectedStudy = JSON.parse(localStorage.getItem('selectedStudy'))
  if (selectedStudy) {
    return selectedStudy.uid
  } else {
    return null
  }
}

export default {
  extractStudyUidFromUrl,
  extractStudyUidFromLocalStorage,
}
