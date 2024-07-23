#!/usr/bin/env node
// Usage: $0 SRC.json [ DST.json ]
// Update JSON document from SRC to DST (or stdout) overwriting properties from environment variables
// if an env var with same name is set and not empty

const fs = require('fs')

const ENCODING = 'utf8'

const args = process.argv.slice(2)

if (args.length < 1 || args.length > 2) {
  console.error('Requires one or two arguments: SRC.json [ DST.json ]')
  process.exit(1)
}
const inputFilename = args.shift()
const outputFilename = args.length ? args.shift() : null

const doc = JSON.parse(fs.readFileSync(inputFilename, { encoding: ENCODING }))

// update all properties of doc form env var if an env var with the same name is set (and not empty)
for (const key in doc) {
  if (key in process.env && process.env[key]) {
    doc[key] = process.env[key]
  }
}

const json = JSON.stringify(doc, null, 4)

if (outputFilename !== null) {
  fs.writeFileSync(outputFilename, json, { encoding: ENCODING })
} else {
  process.stdout.write(json)
}

process.exit(0)
