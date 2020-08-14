<!-- credit to https://babeljs.io/docs/en/babel-cli -->

## Transpiling CarSearch.js from CarSearch_source.js

### Requirements

-   Node.js

_Install babel using node package manager_

```bash
npm install
```

_transpile jsx into javascript using babel_

```bash
npx babel SearchInput_source.js --out-file SearchInput.js --source-maps --presets=@babel/preset-react
```

<!-- TODO - use preact.js -->
