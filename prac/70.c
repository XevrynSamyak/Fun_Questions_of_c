#include <stdio.h>

int main()
{
    char str[100], sub[50];
    int i, j, count = 0;

    printf("Enter the string: ");
    fgets(str, sizeof(str), stdin);

    printf("Enter the substring: ");
    fgets(sub, sizeof(sub), stdin);

    for (i = 0; str[i] != '\0'; i++)
    {
        j = 0;

        while (sub[j] != '\0' && str[i + j] == sub[j])
        {
            j++;
        }

        if (sub[j] == '\0')
        {
            count++;
        }
    }

    printf("Number of occurrences = %d", count);

    return 0;
}
