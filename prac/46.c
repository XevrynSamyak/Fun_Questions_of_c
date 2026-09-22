#include <stdio.h>
#define MAX_SIZE 10

int main() {
    int i, j, a, b;
    int matrix1[MAX_SIZE][MAX_SIZE];
    int matrix2[MAX_SIZE][MAX_SIZE];

    printf("Enter the number of rows: ");
    scanf("%d", &a);

    printf("Enter the number of columns: ");
    scanf("%d", &b);

    // First matrix
    printf("\nEnter values for Matrix 1:\n");

    for (i = 0; i < a; i++) {
        for (j = 0; j < b; j++) {
            printf("Enter number: ");
            scanf("%d", &matrix1[i][j]);
        }
    }

    // Second matrix
    printf("\nEnter values for Matrix 2:\n");

    for (i = 0; i < a; i++) {
        for (j = 0; j < b; j++) {
            printf("Enter number: ");
            scanf("%d", &matrix2[i][j]);
        }
    }

    // Display both matrices
    printf("\nMatrix 1:\n");

    for (i = 0; i < a; i++) {
        for (j = 0; j < b; j++) {
            printf("%d ", matrix1[i][j]);
        }
        printf("\n");
    }

    printf("\nMatrix 2:\n");

    for (i = 0; i < a; i++) {
        for (j = 0; j < b; j++) {
            printf("%d ", matrix2[i][j]);
        }
        printf("\n");
    }

    return 0;
}