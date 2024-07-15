**Government KPIs Web Dashboard**

Objective: Visualize different economic metrics for the Argentinian government in a Python powered Dash/Flask web dashboard using an AWS cloud backend.

**The need for a web dashboard**

Argentina is facing a deep crisis, and constant data is needed to monitor the situation. Public institutions, think tanks, and consultants are hard at work every day, producing countless graphs and reports to make sense of Argentina's situation. In this fast-paced environment, there are hardly any online graphs fed with live data to base your analysis on.

Plus, a new API was launched by the BCRA at the beginning of 2024. It provides excellent metrics for economic analysis, now with the added benefit of being live from the source. This API offers real-time data on inflation, exchange rates, and other key economic indicators, which can be crucial for making timely decisions and understanding the immediate impacts of policy changes.

That's why I decided to take matters into my own hands and start a live web dashboard, fed with the most updated information Argentina has to offer. By building this dashboard, I aim to provide a valuable tool for analysts, policymakers, and anyone interested in staying informed about Argentina's economic situation in real time. This live dashboard will make it easier to spot trends, react to changes quickly, and make more informed decisions.

**Building Production-Level Dashboards**

As a data analyst, I'm always using tools like PowerBI to make data available to stakeholders. But anyone who has used these tools extensively knows that building production-level dashboards can be quite a challenge. The benefits of PowerBI can also be its weaknesses: it's easy for someone with no experience to create something useful, but its high-level nature means it can't abstract as much as a pure programming language. It solves 90% of problems quickly, but the remaining 10% can be extremely difficult, requiring complex workarounds or proving impossible to address. And the lack of effective collaboration tools and robust version control just makes matters worse.

I use extensively python in my day-to-day tasks, so I thought, "There has to be a more programmatic way to create dashboards in python." And, of course, with Python, there are several libraries that can help. I decided to build my project using the Dash library. Streamlit is a simpler option, but I wanted the most customizable dashboard possible. Dash uses Plotly for graphs, so any data analyst familiar with Python can use it, and it wraps everything with Flask to create a simple web app.

As I recently got certified in AWS, I decided to do a cloud deployment in with AWS Elastic Beanstalk and then customize supporting infrastructure going from there.

**Drawing the roadmap.**

The development was completed in the following stages:

**1. ****Feature Listing:** Description of the dashboard features and functionality

**2. ****Sources Definition:** Research about the feasibility of this features based on data availability.

**3. ****Dashboard Design:** Creation of a layout sketch in Figma

**4. ****Web App Development:** Development of the frontend and backend of the web application.

**5. ****Cloud Deployment:** Deployment of the Web App in AWS

**Stage 1: Feature Listing**

The dashboard will serve as a comprehensive tool for analyzing Argentina's economic situation, structured into several tabs. Each tab will focus on different aspects of the economy, providing users with an intuitive way to navigate through various metrics. For the initial phase, I will focus on the Monetary Data tab.

**Monetary Data**

This tab will showcase the most critical data related to monetary policy, allowing users to monitor key economic indicators effectively. The graphs included will feature:

-   Monetary aggregates with month-to-month variation and nominal changes (M0, M1, M2).
-   Central Bank liabilities, including LELIQs and PASEs.
-   Monthly inflation, categorized into core, seasonal, and controlled services.
-   Expected inflation derived from REM and CER bond yields.
-   A comparison of real and nominal monetary policy rates against expected USD devaluation.

**Fiscal Data**

In future iterations, a Fiscal Data tab will be added to provide insights into government finances. This tab will include:

-   Monthly government spending, broken down by concept.
-   Monthly government tax revenues.
-   Monthly debt payments.
-   Gross and net BCRA reserves.
-   Expected fiscal balance projections.

**Financial Data**

Another upcoming tab will focus on Financial Data, offering a snapshot of the financial landscape. Key metrics will include:

-   Country risk assessments.
-   MERVAL index performance and leading stocks.
-   Government bond prices and yields.
-   Exchange rates (official, MEP/CCL, and blue).
-   The multilateral exchange rate.

**Real Economy Data**

Lastly, the Real Economy Data tab will cover broader economic indicators, featuring:

-   Industrial production index with monthly variations.
-   Idle capacity and EMAE (Encuesta Mensual de Actividad Económica).
-   Balance of Payments.
-   Volume of MULC (Mercado Único y Libre de Cambios) operations.

This structured approach will ensure that users can easily access and analyze vital economic indicators, enhancing their understanding of Argentina's economic landscape over time.

**Stage 2****: Sources Definition**

To ensure the dashboard is comprehensive and up to date, I will feed it with data from a combination of sources. I will use the newly launched API from the Central Bank of Argentina (BCRA) to obtain real-time monetary data. For inflation statistics, I will scrape data from INDEC, Argentina's national statistics and census institute. Additionally, I will scrape dollar futures information from MATBA-ROFEX, Argentina's leading futures and options market. By integrating these three sources, the dashboard will provide a holistic view of Argentina's economic landscape, offering users real-time insights into key financial indicators.

To gather the necessary data for the dashboard, I implemented a multi-step process tailored to each source. For the Central Bank of Argentina (BCRA), I utilized Python's requests library to access their API. Initially, I had to map out the API endpoints, as the documentation was sparse. This involved making test requests and analyzing the returned data structures to understand how to extract the relevant monetary data effectively.

For inflation data from INDEC, I employed a combination of Beautiful Soup and requests. First, I used Beautiful Soup to scrape the INDEC website and locate the link to the updated inflation Excel file. After finding the correct link, I used requests to download the file programmatically, ensuring I always have the latest inflation statistics available for the dashboard.

Finally, for dollar futures information from MATBA-ROFEX, I took a different approach. I reverse-engineered their API by inspecting the network requests made by my browser when accessing their website. This involved using browser developer tools to analyze the data being sent and received during interactions, allowing me to construct my own API calls without relying on any public APIs. By following these steps, I ensured that the dashboard is continuously fed with accurate and up-to-date economic data from reliable sources.

**Stage 3: Dashboard Design**

I decided to use Figma to create the web app mockup because it's a powerful design tool widely used in the industry for its versatility and ease of use. Figma excels in UX/UI design, making it perfect for designing a web dashboard. Its intuitive interface allows for rapid prototyping and wireframing, which is essential for planning the layout and user interactions of the dashboard. With Figma, I can create a clean and user-friendly interface that effectively presents Argentina's economic data.

Figma's ability to create detailed designs is invaluable, allowing for a thorough visualization of the user experience before development begins. This ensures the final product is both functional and user-friendly. Additionally, using Figma means adhering to current best practices and industry standards, resulting in a polished and professional web dashboard. Its efficiency in creating detailed designs will streamline the development process, making it easier to bring the project to life.

The design is here:

[**https://www.figma.com/file/rB8B13r6GZiHk2PON9bbsQ/Government-KPIs-Dashboard?type=design&node-id=0%3A1&mode=dev&t=DoRAwaUQXKcogOV6-1**](https://www.figma.com/file/rB8B13r6GZiHk2PON9bbsQ/Government-KPIs-Dashboard?type=design&node-id=0%3A1&mode=dev&t=DoRAwaUQXKcogOV6-1)

**Stage 4: Web App Development**

I'm utilizing Dash and Plotly to create an interactive experience. Plotly allows me to generate detailed visualizations like bar graphs and line charts, which display critical metrics such as base money variation and inflation rates. The code lets me customize these graphs easily, ensuring clarity and effective communication of the data.

Dash is responsible for structuring the web application. It provides components that help organize the layout, such as dcc.Graph for embedding the Plotly figures. This integration means that the graphs are not only visually engaging but also interactive, allowing for a more in-depth exploration of the data.

In addition to static visualizations, Dash supports callbacks that can make the dashboard responsive to user inputs, such as dropdown menus for selecting different economic indicators. This feature enhances the user experience by providing real-time data updates.

**Stage 5: Deployment**

To deploy the web dashboard using AWS Elastic Beanstalk, I took advantage of its streamlined process, which simplifies managing application infrastructure. Here's how I approached the deployment:

1.  **Application Preparation:**

-   I packaged the Dash application along with its dependencies into a single directory. This included the main Python script and a requirements.txt file specifying all necessary libraries.

3.  **Environment Setup:**

-   In the AWS Management Console, I created a new Elastic Beanstalk environment for the application, selecting the Python platform, which is compatible with Dash.

5.  **Uploading the Application:**

-   After setting up the environment, I uploaded the packaged application. Elastic Beanstalk automatically provisions the necessary resources, such as EC2 instances and security groups.

7.  **Configuration:**

-   I configured environment settings to optimize performance, including instance type and scaling options, ensuring the application can handle varying loads efficiently.

9.  **Deployment:**

-   The application was deployed smoothly through Elastic Beanstalk, which initialized everything and made the dashboard accessible online.

11. **Monitoring:**

-   I utilized the Elastic Beanstalk dashboard to monitor application health, manage scaling, and view logs, which helped in maintaining optimal performance and quickly addressing any issues.

With this deployment completed, I can now focus on enhancing the dashboard's features, knowing that Elastic Beanstalk is handling the infrastructure management seamlessly. This allows for efficient delivery of real-time economic insights to users.