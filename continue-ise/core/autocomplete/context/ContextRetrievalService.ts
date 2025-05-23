import { IDE } from "../..";
import {
  AutocompleteCodeSnippet,
  AutocompleteSnippetType,
} from "../snippets/types";
import { HelperVars } from "../util/HelperVars";
import { GetLspDefinitionsFunction } from "../types.js"

import { ImportDefinitionsService } from "./ImportDefinitionsService";
import { getSymbolsForSnippet } from "./ranking";
import { RootPathContextService } from "./RootPathContextService";
import { SimilarCodeContextService } from "./SimilarCodeContextService"; 
import { SimilarUsageContextService } from "./SimilarUsageContextService"; 
export class ContextRetrievalService {
  private importDefinitionsService: ImportDefinitionsService;
  private rootPathContextService: RootPathContextService;
  private similarCodeContextService: SimilarCodeContextService;
  private similarUsageContextService: SimilarUsageContextService;

  constructor(private readonly ide: IDE) {
    this.importDefinitionsService = new ImportDefinitionsService(this.ide);
    this.rootPathContextService = new RootPathContextService(
      this.importDefinitionsService,
      this.ide,
    );
    this.similarCodeContextService = new SimilarCodeContextService(this.ide);
    this.similarUsageContextService = new SimilarUsageContextService();
  }

  public async getSnippetsFromImportDefinitions(
    helper: HelperVars,
  ): Promise<AutocompleteCodeSnippet[]> {
    if (helper.options.useImports === false) {
      return [];
    }

    const importSnippets: AutocompleteCodeSnippet[] = [];
    const fileInfo = this.importDefinitionsService.get(helper.filepath);
    if (fileInfo) {
      const { imports } = fileInfo;
      // Look for imports of any symbols around the current range
      const textAroundCursor =
        helper.fullPrefix.split("\n").slice(-5).join("\n") +
        helper.fullSuffix.split("\n").slice(0, 3).join("\n");
      const symbols = Array.from(getSymbolsForSnippet(textAroundCursor)).filter(
        (symbol) => !helper.lang.topLevelKeywords.includes(symbol),
      );
      for (const symbol of symbols) {
        const rifs = imports[symbol];
        if (Array.isArray(rifs)) {
          const snippets: AutocompleteCodeSnippet[] = rifs.map((rif) => {
            return {
              filepath: rif.filepath,
              content: rif.contents,
              type: AutocompleteSnippetType.Code,
            };
          });

          importSnippets.push(...snippets);
        }
      }
    }

    return importSnippets;
  }

  public async getRootPathSnippets(
    helper: HelperVars,
  ): Promise<AutocompleteCodeSnippet[]> {
    if (!helper.treePath) {
      return [];
    }

    return this.rootPathContextService.getContextForPath(
      helper.filepath,
      helper.treePath,
    );
  }

  public async getSimilarCodeSnippets(
    helper: HelperVars
  ): Promise<AutocompleteCodeSnippet[]> {
    return this.similarCodeContextService.retrieve(helper.cursor, helper.fileLines);
  }

  public async getSimilarUsageSnippets(
    helper: HelperVars,
    getDefinitionsFromLsp: GetLspDefinitionsFunction,
  ): Promise<AutocompleteCodeSnippet[]> {
    return this.similarUsageContextService.retrieve(
      helper.filepath,
      helper.fullPrefix + helper.fullSuffix,
      helper.fullPrefix.length,
      this.ide,
      helper.lang,
      getDefinitionsFromLsp,
    );
  }
}
