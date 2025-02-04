# Note

- LSP can not get definition for import * in java, only for import package.AClass

- Continue wrong implement constructAutocompletePrompt

```js
finalSnippets = fillPromptWithSnippets(
    scoredSnippets,
    helper.maxSnippetTokens,
    helper.modelName,
);
```

`scoredSnippets` should be `finalSnippets`

- Continue wrong implement mergeSnippetsByRange

```js
const merged: Required<AutocompleteSnippet>[] = [];

while (sorted.length > 0) {
    const next = sorted.shift()!;
    const last = merged[merged.length - 1];
```

merged is initial empty list, so last is undefined
=> It still work in typescript

- Continue formatExternalSnippet

```js
export function formatExternalSnippet(
  filepath: string,
  snippet: string,
  language: AutocompleteLanguageInfo,
) {
  const comment = language.singleLineComment;
  const lines = [
    `${comment} Path: ${getBasename(filepath)}`,
    ...snippet
      .trim()
      .split("\n")
      .map((line) => `${comment} ${line}`),
    comment,
  ];
  return lines.join("\n");
}
```

Why need to getBaseName?

- Need to install Language Server for Java extension in VSCode to use additional context

