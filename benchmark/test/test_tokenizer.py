from transformers import LlamaTokenizerFast, AutoTokenizer

code = """/*
 * Copyright (c) 2022, Harald Kuhr
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * * Redistributions of source code must retain the above copyright notice,
 *   this list of conditions and the following disclaimer.
 *
 * * Redistributions in binary form must reproduce the above copyright notice,
 *   this list of conditions and the following disclaimer in the documentation
 *   and/or other materials provided with the distribution.
 *
 * * Neither the name of the copyright holder nor the names of its
 *   contributors may be used to endorse or promote products derived from
 *   this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ""AS IS""
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

package net.burningtnt.webp.vp8l.huffman;

import net.burningtnt.webp.utils.LSBBitInputStream;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Represents a single huffman tree as a table.
 * <p>
 * Decoding a symbol just involves reading bits from the input stream and using that read value to index into the
 * lookup table.
 * <p>
 * Code length and the corresponding symbol are packed into one array element (int).
 * This is done to avoid the overhead and the fragmentation over the whole heap involved with creating objects
 * of a custom class. The upper 16 bits of each element are the code length and lower 16 bits are the symbol.
 * <p>
 * The max allowed code length by the WEBP specification is 15, therefore this would mean the table needs to have
 * 2^15 elements. To keep a reasonable memory usage, instead the lookup table only directly holds symbols with code
 * length up to {@code LEVEL1_BITS} (Currently 8 bits). For longer codes the lookup table stores a reference to a
 * second level lookup table. This reference consists of an element with length as the max length of the level 2
 * table and value as the index of the table in the list of level 2 tables.
 * <p>
 * Reading bits from the input is done in a least significant bit first way (LSB) way, therefore the prefix of the
 * read value of length i is the lowest i bits in inverse order.
 * The lookup table is directly indexed by the {@code LEVEL1_BITS} next bits read from the input (i.e. the bits
 * corresponding to next code are inverse suffix of the read value/index).
 * So for a code length of l all values with the lowest l bits the same need to decode to the same symbol
 * regardless of the {@code (LEVEL1_BITS - l)} higher bits. So the lookup table needs to have the entry of this symbol
 * repeated every 2^(l + 1) spots starting from the bitwise inverse of the code.
 *
 * @author Simon Kammermeier
 */
public final class HuffmanTable {
    private static final int LEVEL1_BITS = 8;
    /**
     * Symbols of the L-code in the order they need to be read
     */
    private static final int[] L_CODE_ORDER = {17, 18, 0, 1, 2, 3, 4, 5, 16, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15};
    private final int[] level1 = new int[1 << LEVEL1_BITS];
    private final List<int[]> level2 = new ArrayList<>();

    /**
     * Build a Huffman table by reading the encoded symbol lengths from the reader
     *
     * @param lsbBitReader the reader to read from
     * @param alphabetSize the number of symbols in the alphabet to be decoded by this huffman table
     * @throws IOException when reading produces an exception
     */
    public HuffmanTable(LSBBitInputStream lsbBitReader, int alphabetSize) throws IOException {
        boolean"""

deepseek_tokenizer = AutoTokenizer.from_pretrained("deepseek-ai/deepseek-coder-6.7b-base")
llama_tokenizer = LlamaTokenizerFast.from_pretrained("hf-internal-testing/llama-tokenizer")

print(len(deepseek_tokenizer(code)["input_ids"]))
print(len(llama_tokenizer(code)["input_ids"]))