# Introduction

This is the souce code of my thesis at University of Engineering and Technology (VNU). I leverage Continue (a open source project - Code assistant Extension for IDE like VSCode and Jetbrain's products). I develop my self research and improvement upon source code base.

# Details

Will be added soon

# Known issues

- If the Java project has multiple function with the same name within a file, the gotoDefinition function will return the first function that Language Server has parsed
- Execute provider function (related to LSP) has cache machanism. Because the cache key is combined just only by position of cursor and uri of file, so if you move the cursor to the same position, the cache will be used even if the content of that position is changed.
- Because incremental indexing for similar code chunk will save the chunks that has different different hash values so if a chunk is just changed a little bit, it will be indexed as a new chunk. This may cause a lot of "duplicate" chunks with almost same value if retrieval in this case -> the retrieval result will be not good.

# Note

- The base implementation don't sort the similarity of retrieval code to the complete window (may be because it only retrieves definition of class, function)

- Sliding window size (128 tokens)

# TODO
- [ ] Run exist test cases for autocomplete feature
- [ ] Handle getAllSnippets function correctly
- [ ] Change racePromise to 100-200ms 
# Continue

<div align="center">

![Continue logo](media/readme.png)

</div>

<h1 align="center">Continue</h1>

<div align="center">

**[Continue](https://docs.continue.dev) is the leading open-source AI code assistant. You can connect any models and any context to build custom autocomplete and chat experiences inside [VS Code](https://marketplace.visualstudio.com/items?itemName=Continue.continue) and [JetBrains](https://plugins.jetbrains.com/plugin/22707-continue-extension)**

</div>

<div align="center">

<a target="_blank" href="https://opensource.org/licenses/Apache-2.0" style="background:none">
    <img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" style="height: 22px;" />
</a>
<a target="_blank" href="https://docs.continue.dev" style="background:none">
    <img src="https://img.shields.io/badge/continue_docs-%23BE1B55" style="height: 22px;" />
</a>
<a target="_blank" href="https://discord.gg/vapESyrFmJ" style="background:none">
    <img src="https://img.shields.io/badge/discord-join-continue.svg?labelColor=191937&color=6F6FF7&logo=discord" style="height: 22px;" />
</a>

<p></p>

## Chat

[Chat](https://continue.dev/docs/chat/how-to-use-it) makes it easy to ask for help from an LLM without needing to leave the IDE

![chat](docs/static/img/chat.gif)

## Autocomplete

[Autocomplete](https://continue.dev/docs/autocomplete/how-to-use-it) provides inline code suggestions as you type

![autocomplete](docs/static/img/autocomplete.gif)

## Edit

[Edit](https://continue.dev/docs/edit/how-to-use-it) is a convenient way to modify code without leaving your current file

![edit](docs/static/img/edit.gif)

## Actions

[Actions](https://continue.dev/docs/actions/how-to-use-it) are shortcuts for common use cases.

![actions](docs/static/img/actions.gif)

</div>

## Getting Started

Learn about how to install and use Continue in the docs [here](https://continue.dev/docs/getting-started/install)

## Contributing

Check out the [contribution ideas board](https://github.com/orgs/continuedev/projects/2), read the [contributing guide](https://github.com/continuedev/continue/blob/main/CONTRIBUTING.md), and join [#contribute on Discord](https://discord.gg/vapESyrFmJ)

## License

[Apache 2.0 © 2023-2024 Continue Dev, Inc.](./LICENSE)
