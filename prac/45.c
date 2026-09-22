#include <stdio.h>
#define MAX_SIZE 10
int main(){
    int i,j,a,b;
    int matrix[MAX_SIZE][MAX_SIZE];
    printf("enter the number of rows: ");
    scanf("%d",&a);
    printf("enter the number of columns: ");
    scanf("%d",&b);
    printf("enter the elements of the matrix:\n");
    for(i=0;i<a;i++){
        for(j=0;j<b;j++){
            scanf("%d",&matrix[i][j]);
        }
    }
    for (j = 0; j < b; j++) {
       int smallest = matrix[0][j];
       for (i = 1; i < a; i++)
   {
   if (matrix[i][j] < smallest){
      smallest = matrix[i][j];
    }
    }
       printf("Smallest element in column %d = %d\n",j + 1, smallest);
    }
    return 0;
}