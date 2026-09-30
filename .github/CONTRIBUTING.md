# Contributing to Cipher Bridge

Cipher Bridge is a fork of [KeePassXC-Browser](https://github.com/keepassxreboot/keepassxc-browser)
that talks to [Cipher](https://github.com/steeb-k/cipher) instead of
KeePassXC. These are guidelines, not rules; use your best judgment, and feel
free to propose changes to this document in a pull request.

## How can I contribute?

### Feature requests and bug reports

Both go to the [issue tracker](https://github.com/steeb-k/cipher-browser/issues).
Before filing a bug, check whether it has already been reported; if it has,
add to the existing issue rather than opening a duplicate. Include the debug
information from the extension's settings page (About → Copy debug info) and
never include screenshots of real credentials.

A problem that reproduces with KeePassXC-Browser and KeePassXC as well is
almost certainly upstream's, and is best reported there.

### Pull requests

Pull requests are welcome. Keep them focused, describe why the change is
needed, and say how you tested it. Changes to behaviour shared with
KeePassXC-Browser should be kept in Cipher-specific files where possible
(see `content/cipher-icons.js` for the pattern), so that upstream files stay
easy to compare against.

### Translations

Strings live in `keepassxc-browser/_locales/`. A pull request that adds new
strings only needs to touch `_locales/en/messages.json`; translations for
other languages are welcome as pull requests against the matching file.

### Architecture

The extension's structure is described in KeePassXC-Browser's
[Extension details](https://github.com/keepassxreboot/keepassxc-browser/wiki/Extension-details)
wiki page, which still applies. The messaging protocol is documented in
[keepassxc-protocol.md](../keepassxc-protocol.md).

## Styleguides

### Git commit messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to…" not "Moves cursor to…")
* Limit the first line to 72 characters or less
* Explain why in the body, not just what
* If your pull request fixes an existing issue, add "Fixes #ISSUENUMBER" to the description

### Coding styleguide

The coding style is enforced with ESLint: `npm run lint`. The main
conventions:

#### Naming convention
`lowerCamelCase` for functions, objects and variables; `UpperCamelCase` for
classes and enum-like objects; `ALL_CAPS` for global constants and enum-like
object values.

#### Indentation
- JavaScript files (*.js): 4 spaces
- HTML files: 2 spaces
- JSON files: 2 spaces
- TypeScript files (*.ts): 2 spaces

#### Global/const variables
```javascript
const TIMEOUT_VALUE = 2000;
const DEFAULT_VALUE = 'all';
```

#### Classes
```javascript
class Icon {
    constructor(databaseState) {
        this.databaseState = databaseState;
        this.icon = null;
    }
}
```

#### Enum-like Objects
```javascript
const ManualFill = {
    NONE: 0,
    PASSWORD: 1,
    BOTH: 2
};
```

#### Braces
```javascript
if (condition) {
    doSomething();
} else {
    doSomethingElse();
}

const exampleFunction = async function() {
    doSomething();
};
```

#### Multiple conditions
```javascript
if (condition1 === condition2
    || condition3 === condition4
    || condition5 === condition6) {
    doSomething();
}

if (['text1', 'text2', 'text3'].includes(inputText)) {
    doSomething();
}
```

#### Variables

Always use `const` and `let` to define a variable. Do not use `var`.
