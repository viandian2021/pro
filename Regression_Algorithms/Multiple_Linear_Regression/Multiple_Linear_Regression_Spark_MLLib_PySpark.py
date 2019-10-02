# -*- coding: utf-8 -*-
"""Multiple_Linear_Regression_Spark_MLLib_PySpark.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1XRhsFkp9z3wHfeKMwmGRbJvnQMyoloJd
"""

# Install all the dependencies in Colab environment i.e. Apache Spark 2.4.4 with hadoop 2.7, Java 8 and Findspark to locate the spark in the system
!apt-get install openjdk-8-jdk-headless -qq > /dev/null
!wget -q http://apache.osuosl.org/spark/spark-2.4.4/spark-2.4.4-bin-hadoop2.7.tgz
!tar xf spark-2.4.4-bin-hadoop2.7.tgz
!pip install -q findspark

# Setup Environment Variables
import os
os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-8-openjdk-amd64"
os.environ["SPARK_HOME"] = "/content/spark-2.4.4-bin-hadoop2.7"

# Start Spark Session
import findspark
findspark.init()
from pyspark.sql import SparkSession
spark = SparkSession.builder.master("local[*]").getOrCreate()

#Necessary Python Libraries
import pandas as pd

#Upload Student_Grades_Data.csv file from local system to remote colab location
from google.colab import files
files.upload()

#Loading the Student_Grades_Data.csv file, uploaded in previous step
data = spark.read.csv('Restaurant_Profit_Data.csv', header=True, inferSchema=True)

#Taking a look at data type of each column to see what data types inferSchema=TRUE paramter has set for each column
data.printSchema()

#Display first few rows of data
data.show()

#Display data types of the data columns.
data.dtypes

#Create features storing categorical & numerical variables, omitting the last column
categorical_cols = [item[0] for item in data.dtypes if item[1].startswith('string')]
print(categorical_cols)

numerical_cols = [item[0] for item in data.dtypes if item[1].startswith('int') | item[1].startswith('double')][:-1]
print(numerical_cols)

#Print number of categorical as well as numerical features.
print(str(len(categorical_cols)) + '  categorical features')
print(str(len(numerical_cols)) + '  numerical features')

# First using StringIndexer to convert string/text values into numerical values followed by OneHotEncoderEstimator 
# Spark MLLibto convert each Stringindexed or transformed values into One Hot Encoded values.
# VectorAssembler is being used to assemble all the features into one vector from multiple columns that contain type double 
# Also appending every step of the process in a stages array
from pyspark.ml.feature import StringIndexer, OneHotEncoderEstimator, VectorAssembler
stages = []
for categoricalCol in categorical_cols:
    stringIndexer = StringIndexer(inputCol = categoricalCol, outputCol = categoricalCol + 'Index')
    OHencoder = OneHotEncoderEstimator(inputCols=[stringIndexer.getOutputCol()], outputCols=[categoricalCol + "_catVec"])
stages += [stringIndexer, OHencoder]
assemblerInputs = [c + "_catVec" for c in categorical_cols] + numerical_cols
Vectassembler = VectorAssembler(inputCols=assemblerInputs, outputCol="features")
stages += [Vectassembler]

# Using a Spark MLLib pipeline to apply all the stages of transformation
from pyspark.ml import Pipeline
cols = data.columns
pipeline = Pipeline(stages = stages)
pipelineModel = pipeline.fit(data)
data = pipelineModel.transform(data)
selectedCols = ['features']+cols
data = data.select(selectedCols)
pd.DataFrame(data.take(5), columns=data.columns)

#Display the data having additional column named features. Since it's a multiple linear regression problem, hence all the
# independent variable values are shown as one vector
data.show()

#Select only Features and Label from previous dataset as we need these two entities for building machine learning model
finalized_data = data.select("features","Profit")

finalized_data.show()

#Split the data into training and test model with 70% obs. going in training and 30% in testing
train_dataset, test_dataset = finalized_data.randomSplit([0.7, 0.3])

#Import Linear Regression class called LinearRegression
from pyspark.ml.regression import LinearRegression

#Create the Multiple Linear Regression object named MLR having feature column as features and Label column as Profit
MLR = LinearRegression(featuresCol="features", labelCol="Profit")

#Train the model on the training using fit() method.
model = MLR.fit(train_dataset)

#Predict the Profit on Test Dataset using the evulate method
pred = model.evaluate(test_dataset)

#Show the predicted Grade values along side actual Grade values
pred.predictions.show()

#Find out coefficient value
coefficient = model.coefficients
print ("The coefficients of the model are : %a" %coefficient)

#Find out intercept Value
intercept = model.intercept
print ("The Intercept of the model is : %f" %intercept)

#Evaluate the model using metric like Mean Absolute Error(MAE), Root Mean Square Error(RMSE) and R-Square
from pyspark.ml.evaluation import RegressionEvaluator
evaluation = RegressionEvaluator(labelCol="Profit", predictionCol="prediction")

# r2 - coefficient of determination
r2 = evaluation.evaluate(pred.predictions, {evaluation.metricName: "r2"})
print("r2: %.3f" %r2)

#Create Unlabeled dataset  to contain only feature column
unlabeled_dataset = test_dataset.select('features')

#Display the content of unlabeled_dataset
unlabeled_dataset.show()

#Predict the model output for fresh & unseen test data using transform() method
new_predictions = model.transform(unlabeled_dataset)

#Display the new prediction values
new_predictions.show()
