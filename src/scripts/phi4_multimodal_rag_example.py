# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Phi-4-multimodal-instruct RAG (Retrieval Augmented Generation) Example

This example shows how to use Phi-4-multimodal-instruct with Azure AI Search
for Retrieval Augmented Generation with both text and multimodal inputs.

Based on Microsoft's PhiCookBook E2E example.
"""

import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import (
    SystemMessage,
    UserMessage,
    TextContentItem,
    ImageContentItem,
    ImageUrl,
    ImageDetailLevel,
)
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from typing import List, Optional
import base64


class Phi4MultimodalRAG:
    """
    A class for performing RAG with Phi-4-multimodal-instruct and Azure AI Search.
    """
    
    def __init__(
        self,
        inference_endpoint: str,
        inference_key: str,
        search_endpoint: str,
        search_index: str,
        search_key: str
    ):
        """
        Initialize the RAG system with Azure endpoints.
        
        Args:
            inference_endpoint: Azure AI Inference endpoint for Phi-4-multimodal
            inference_key: API key for inference endpoint
            search_endpoint: Azure AI Search endpoint
            search_index: Name of the search index
            search_key: API key for search endpoint
        """
        # Initialize chat client for Phi-4-multimodal
        self.chat_client = ChatCompletionsClient(
            endpoint=inference_endpoint,
            credential=AzureKeyCredential(inference_key),
        )
        
        # Initialize search client
        self.search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=search_index,
            credential=AzureKeyCredential(search_key)
        )
    
    def retrieve_documents(self, query: str, top: int = 3) -> List[str]:
        """
        Retrieve relevant documents from Azure AI Search.
        
        Args:
            query: Search query
            top: Number of documents to retrieve
            
        Returns:
            List of document contents
        """
        # Create vector query for semantic search
        vector_query = VectorizableTextQuery(
            text=query,
            k_nearest_neighbors=top,
            fields="text_vector"  # Assumes your index has a text_vector field
        )
        
        # Perform search
        results = self.search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            select=["content"],
            top=top
        )
        
        # Extract document contents
        documents = [doc["content"] for doc in results]
        return documents
    
    def format_context(self, documents: List[str]) -> str:
        """
        Format retrieved documents into a context string.
        
        Args:
            documents: List of document contents
            
        Returns:
            Formatted context string
        """
        context = "Retrieved Documents:\n\n"
        for i, doc in enumerate(documents, 1):
            context += f"Document {i}:\n{doc}\n\n"
        return context
    
    def text_only_rag(self, query: str, system_prompt: Optional[str] = None) -> str:
        """
        Perform text-only RAG with Phi-4-multimodal.
        
        Args:
            query: User query
            system_prompt: Optional system prompt
            
        Returns:
            Generated response
        """
        # Retrieve relevant documents
        documents = self.retrieve_documents(query)
        context = self.format_context(documents)
        
        # Default system prompt for RAG
        if not system_prompt:
            system_prompt = (
                "You are a helpful AI assistant. Use the retrieved documents "
                "to answer questions. If the answer cannot be found in the "
                "documents, say so."
            )
        
        # Create messages
        messages = [
            SystemMessage(content=system_prompt),
            UserMessage(
                content=[
                    TextContentItem(
                        text=f"{context}\n\nQuestion: {query}\n\nAnswer:"
                    )
                ]
            )
        ]
        
        # Generate response
        response = self.chat_client.complete(
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def multimodal_rag(
        self,
        query: str,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Perform multimodal RAG with text and image inputs.
        
        Args:
            query: User query
            image_url: URL of the image (optional)
            image_base64: Base64 encoded image (optional)
            system_prompt: Optional system prompt
            
        Returns:
            Generated response
        """
        # Retrieve relevant documents
        documents = self.retrieve_documents(query)
        context = self.format_context(documents)
        
        # Default system prompt
        if not system_prompt:
            system_prompt = (
                "You are a helpful AI assistant that can analyze both text "
                "and images. Use the retrieved documents and any provided "
                "images to answer questions comprehensively."
            )
        
        # Build user message content
        user_content = []
        
        # Add image if provided
        if image_url:
            user_content.append(
                ImageContentItem(
                    image_url=ImageUrl(
                        url=image_url,
                        detail=ImageDetailLevel.HIGH
                    )
                )
            )
        elif image_base64:
            user_content.append(
                ImageContentItem(
                    image_url=ImageUrl(
                        url=f"data:image/jpeg;base64,{image_base64}",
                        detail=ImageDetailLevel.HIGH
                    )
                )
            )
        
        # Add text content
        user_content.append(
            TextContentItem(
                text=f"{context}\n\nQuestion: {query}\n\nAnswer:"
            )
        )
        
        # Create messages
        messages = [
            SystemMessage(content=system_prompt),
            UserMessage(content=user_content)
        ]
        
        # Generate response
        response = self.chat_client.complete(
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def multimodal_rag_with_local_model(
        self,
        query: str,
        image_path: Optional[str] = None,
        audio_path: Optional[str] = None
    ) -> str:
        """
        Example of multimodal RAG using local Phi-4 model (not Azure endpoint).
        This shows how to combine retrieval with local model inference.
        """
        from transformers import AutoModelForCausalLM, AutoProcessor
        from PIL import Image
        import soundfile as sf
        
        # Retrieve relevant documents
        documents = self.retrieve_documents(query)
        context = self.format_context(documents)
        
        # Load local model
        model_id = "microsoft/Phi-4-multimodal-instruct"
        processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map="cuda",
            torch_dtype="auto",
            trust_remote_code=True,
            attn_implementation='flash_attention_2',
        )
        
        # Prepare prompt with placeholders
        user_content = ""
        images = []
        audios = None
        
        # Add image if provided
        if image_path:
            user_content += "<|image_1|>"
            image = Image.open(image_path).convert('RGB')
            images = [image]
        
        # Add audio if provided
        if audio_path:
            user_content += "<|audio_1|>"
            audio_data, sample_rate = sf.read(audio_path)
            audios = [(audio_data, sample_rate)]
        
        # Add context and question
        user_content += f"\n{context}\n\nQuestion: {query}\n\nAnswer:"
        
        # Format messages
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Use the retrieved documents to answer questions."},
            {"role": "user", "content": user_content}
        ]
        
        prompt = processor.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Prepare inputs
        inputs_dict = {"text": prompt, "return_tensors": "pt"}
        if images:
            inputs_dict["images"] = images
        if audios:
            inputs_dict["audios"] = audios
        
        inputs = processor(**inputs_dict).to("cuda")
        
        # Generate response
        generate_ids = model.generate(
            **inputs,
            max_new_tokens=1000,
            temperature=0.7,
            do_sample=True,
            eos_token_id=processor.tokenizer.eos_token_id,
        )
        
        # Decode response
        generate_ids = generate_ids[:, inputs['input_ids'].shape[1]:]
        response = processor.batch_decode(
            generate_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]
        
        return response


# Example usage
def main():
    """
    Example of using the Phi4MultimodalRAG class.
    """
    # Initialize RAG system (replace with your actual endpoints and keys)
    rag = Phi4MultimodalRAG(
        inference_endpoint=os.environ.get("AZURE_INFERENCE_ENDPOINT"),
        inference_key=os.environ.get("AZURE_INFERENCE_CREDENTIAL"),
        search_endpoint=os.environ.get("AZURE_SEARCH_ENDPOINT"),
        search_index=os.environ.get("AZURE_SEARCH_INDEX"),
        search_key=os.environ.get("AZURE_SEARCH_KEY")
    )
    
    # Example 1: Text-only RAG
    print("=== Text-only RAG ===")
    response = rag.text_only_rag(
        query="What are the benefits of renewable energy?"
    )
    print(f"Response: {response}\n")
    
    # Example 2: Multimodal RAG with image URL
    print("=== Multimodal RAG with Image ===")
    response = rag.multimodal_rag(
        query="What does this chart show about renewable energy trends?",
        image_url="https://example.com/renewable-energy-chart.jpg"
    )
    print(f"Response: {response}\n")
    
    # Example 3: Multimodal RAG with base64 image
    print("=== Multimodal RAG with Base64 Image ===")
    # Read and encode image
    with open("local_chart.jpg", "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode()
    
    response = rag.multimodal_rag(
        query="Analyze this data visualization",
        image_base64=image_base64
    )
    print(f"Response: {response}\n")


if __name__ == "__main__":
    main()