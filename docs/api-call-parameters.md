## API Call Parameters

For every resume that goes through Talentika, the system makes one call to OpenAI to do the actual screening. A few settings control how that call behaves. We kept these settings the same for the whole study so that any difference in the results comes from the resumes themselves and not from changes in how we asked the model.

### Model

We used **GPT-4o mini**. We picked it over the bigger GPT-4o for a few reasons. It supports the structured output feature we rely on, where the model is forced to answer in a fixed format instead of free text. It is also much cheaper per request, which matters because small and medium HR teams (the kind of users Talentika is built for) cannot afford a premium model on every applicant. Public benchmarks also suggested that for a short task like matching a resume to a job, the quality difference between the two models is small.

### Messages

Each request to the model has two parts: a *system message* and a *user message*.

The **system message** is the same for every applicant. It tells the model to act as a talent acquisition analyst, explains the task, and lays out the rubric for the three possible labels (*Suitable*, *Potentially Suitable*, and *Unsuitable*) with definitions for each. It also gives the model two rules. First, if the candidate fails something marked as "required," lean toward *Unsuitable*. Second, take the screening question answers into account, since weak or evasive answers should lower the rating. When the resume was uploaded in bulk and no contact details were provided by the recruiter, an extra line is added asking the model to read the name, email, and phone number from the top of the resume, and to leave fields blank if it cannot find them.

The **user message** is built fresh for each applicant. It always has the same four sections in the same order: the job title and description, the list of qualifications grouped by category, the candidate's answers to the screening questions, and the resume text from the OCR step. Keeping the layout the same for everyone means the model is comparing apples to apples.

### Response Format

Instead of letting the model reply with free text, we ask it to return a structured object. That object includes a short summary, a list of notable traits, a list of key skills, the final classification, and a deeper breakdown with strengths, areas for development, work experience, education, and certifications. The classification field can only take one of three values (*suitable*, *potentially suitable*, or *unsuitable*), so the model cannot make up a new category, return a synonym, or leave the field empty. This is what makes the labels easy to count and analyse later.

### Generation Parameters

We left the other generation settings (*temperature*, *top-p*, *maximum tokens*, *presence penalty*, and *frequency penalty*) at their OpenAI defaults. This was on purpose. The structured output already controls the shape of the reply, and we did not want to tune the rest, because a typical HR team picking up an off the shelf model would not tune them either. Using the defaults shows what the model does out of the box, which is closer to what real users would actually experience.

### Authentication

The system signs in to OpenAI using an API key that is read from an environment variable. The key is never written into the source code or shared between researchers. Each person who reproduces the study creates their own key from their own OpenAI account. For this study, we created a key called *talentika* through the OpenAI Platform on April 27, 2026, gave it full project permissions, and used only that key for the entire data collection.

![Figure X. The dedicated *talentika* API key as listed in the OpenAI Platform console, showing its active status, creation date, and last used date.](./images/openai-api-key.png)

### Operational Footprint

To show how much the system actually used in practice, the numbers below come straight from the OpenAI Platform usage dashboard for our project key. Between May 5 and May 20, 2026, the backend made **66 requests** to the chat completions endpoint, used **104,589 input tokens**, and spent a total of **US $0.03**. The running total for May 2026 was **US $0.04** against a credit balance of **US $4.65**. This shows that GPT-4o mini is well within reach for the kind of volume a small or medium HR team would generate. All 66 requests went through the "Responses and Chat Completions" endpoint. No image, audio, web search, or file search calls were made, which confirms that the screening pipeline only touches one narrow part of the OpenAI platform.

![Figure X. The OpenAI Platform home dashboard for the project, summarising the monthly spend and remaining credit balance.](./images/openai-home.png)

![Figure X. The OpenAI Platform usage dashboard for the data collection window, showing total spend, total tokens consumed, and the distribution of requests over time.](./images/openai-usage.png)

### Reproducibility Note

Because the default temperature in OpenAI is not zero, the model's answers are not perfectly repeatable. Sending the same resume against the same job on two different days can sometimes give a different label. Researchers who want to reproduce the study should either average their results across several runs, or set the temperature to zero and pass a fixed random seed to get a consistent baseline. They should also keep in mind that `gpt-4o-mini` is a moving target on OpenAI's side. OpenAI can quietly update the model behind that name, so exact label by label reproduction outside our data collection window is not guaranteed even with the same inputs.
