import { IDE, RangeInFileWithContents } from "../..";
import { PrecalculatedLruCache } from "../../util/LruCache";
import {
  getFullLanguageName,
  getParserForFile,
  getQueryForFile,
} from "../../util/treeSitter";

interface FileInfo {
  imports: { [key: string]: RangeInFileWithContents[] };
}

export class ImportDefinitionsService {
  static N = 10;

  private cache: PrecalculatedLruCache<FileInfo> =
    new PrecalculatedLruCache<FileInfo>(
      this._getFileInfo.bind(this),
      ImportDefinitionsService.N,
    );

  constructor(private readonly ide: IDE) {
    ide.onDidChangeActiveTextEditor((filepath) => {
      this.cache.initKey(filepath);
    });
  }

  get(filepath: string): FileInfo | undefined {
    return this.cache.get(filepath);
  }

  // This is implementation to get information of imported object to a file (functions, classes)
  private async _getFileInfo(filepath: string): Promise<FileInfo | null> {
    if (filepath.endsWith(".ipynb")) {
      // Commenting out this line was the solution to https://github.com/continuedev/continue/issues/1463
      return null;
    }

    const parser = await getParserForFile(filepath);
    if (!parser) {
      return {
        imports: {},
      };
    }

    let fileContents: string | undefined = undefined;
    try {
      fileContents = await this.ide.readFile(filepath);
    } catch (err) {
      // File removed
      return null;
    }

    // Use tree-sitter to parse only 10000 first characters of a file or first 100 rows
    // because import sentence normally is at the beginning of a file.
    const ast = parser.parse(fileContents, undefined, {
      includedRanges: [
        {
          startIndex: 0,
          endIndex: 10_000,
          startPosition: { row: 0, column: 0 },
          endPosition: { row: 100, column: 0 },
        },
      ],
    });
    const language = getFullLanguageName(filepath);
    const query = await getQueryForFile(
      filepath,
      `import-queries/${language}.scm`,
    );
    if (!query) {
      return {
        imports: {},
      };
    }

    const matches = query?.matches(ast.rootNode);

    const fileInfo: FileInfo = {
      imports: {},
    };
    for (const match of matches) {
      const startPosition = match.captures[0].node.startPosition;
      const defs = await this.ide.gotoDefinition({
        filepath,
        position: { 
          line: startPosition.row,
          character: startPosition.column,
        },
      });

      for (const def of defs) {
        console.log("A definition:");
        console.log(def.filepath);
        console.log(def.range.start.line, def.range.start.character);
        console.log(def.range.end.line, def.range.end.character);
        console.log("============")
      }

      fileInfo.imports[match.captures[0].node.text] = await Promise.all(
        defs.map(async (def) => ({
          ...def,
          contents: await this.ide.readRangeInFile(def.filepath, def.range),
        })),
      );
    }

    return fileInfo;
  }
}
