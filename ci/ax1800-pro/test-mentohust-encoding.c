#include <assert.h>
#include <stdlib.h>
#include <string.h>

#include "strnormalize.h"

static void expect_text(const char *input, unsigned int input_len,
                        const char *expected, unsigned int expected_len)
{
    char *output = NULL;
    unsigned int output_len = 0;

    assert(text_to_utf8(input, input_len, &output, &output_len) == 0);
    assert(output != NULL);
    assert(output_len == expected_len);
    assert(memcmp(output, expected, expected_len) == 0);
    assert(output[output_len] == '\0');
    free(output);
}

int main(void)
{
    static const char utf8_chinese[] = "\xe4\xb8\xad\xe6\x96\x87";
    static const char gbk_chinese[] = "\xd6\xd0\xce\xc4";
    static const char utf8_emoji[] = "\xf0\x9f\x8c\x90";
    static const char ascii[] = "MentoHUST status";

    expect_text(utf8_chinese, sizeof(utf8_chinese) - 1,
                utf8_chinese, sizeof(utf8_chinese) - 1);
    expect_text(gbk_chinese, sizeof(gbk_chinese) - 1,
                utf8_chinese, sizeof(utf8_chinese) - 1);
    expect_text(utf8_emoji, sizeof(utf8_emoji) - 1,
                utf8_emoji, sizeof(utf8_emoji) - 1);
    expect_text(ascii, sizeof(ascii) - 1,
                ascii, sizeof(ascii) - 1);
    return 0;
}
