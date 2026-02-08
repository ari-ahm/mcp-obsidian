import requests
import urllib.parse
import os
import urllib3
from typing import Any

# Suppress insecure request warnings since we are using self-signed certs locally
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Obsidian():
    def __init__(
            self, 
            api_key: str,
            protocol: str = os.getenv('OBSIDIAN_PROTOCOL', 'https').lower(),
            host: str = str(os.getenv('OBSIDIAN_HOST', '127.0.0.1')),
            port: int = int(os.getenv('OBSIDIAN_PORT', '27124')),
            verify_ssl: bool = False,
        ):
        self.api_key = api_key
        
        if protocol == 'http':
            self.protocol = 'http'
        else:
            self.protocol = 'https' # Default to https for any other value, including 'https'

        self.host = host
        self.port = port
        self.verify_ssl = verify_ssl
        self.timeout = (3, 6)

    def get_base_url(self) -> str:
        return f'{self.protocol}://{self.host}:{self.port}'
    
    def _get_headers(self) -> dict:
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }
        return headers

    def _safe_call(self, f) -> Any:
        try:
            return f()
        except requests.HTTPError as e:
            error_data = e.response.json() if e.response.content else {}
            code = error_data.get('errorCode', e.response.status_code) 
            message = error_data.get('message', str(e))
            raise Exception(f"Obsidian API Error {code}: {message}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    def list_files_in_vault(self) -> Any:
        url = f"{self.get_base_url()}/vault/"
        
        def call_fn():
            response = requests.get(url, headers=self._get_headers(), verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()

            return response.json()['files']

        return self._safe_call(call_fn)

        
    def list_files_in_dir(self, dirpath: str) -> Any:
        # FIX: Strip slashes to prevent double-slash errors (e.g. "folder//")
        clean_path = dirpath.strip("/")
        url = f"{self.get_base_url()}/vault/{clean_path}/"
        
        def call_fn():
            response = requests.get(url, headers=self._get_headers(), verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()['files']

        return self._safe_call(call_fn)

    def get_file_contents(self, filepath: str) -> Any:
        # FIX: Ensure clean path
        clean_path = filepath.strip("/")
        url = f"{self.get_base_url()}/vault/{clean_path}"
    
        def call_fn():
            response = requests.get(url, headers=self._get_headers(), verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            return response.text

        return self._safe_call(call_fn)
    
    def get_batch_file_contents(self, filepaths: list[str]) -> str:
        """Get contents of multiple files and concatenate them with headers.
        
        Args:
            filepaths: List of file paths to read
            
        Returns:
            String containing all file contents with headers
        """
        result = []
        
        for filepath in filepaths:
            try:
                content = self.get_file_contents(filepath)
                result.append(f"# {filepath}\n\n{content}\n\n---\n\n")
            except Exception as e:
                # Add error message but continue processing other files
                result.append(f"# {filepath}\n\nError reading file: {str(e)}\n\n---\n\n")
                
        return "".join(result)

    def search(self, query: str, context_length: int = 100) -> Any:
        url = f"{self.get_base_url()}/search/simple/"
        params = {
            'query': query,
            'contextLength': context_length
        }
        
        def call_fn():
            response = requests.post(url, headers=self._get_headers(), params=params, verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        return self._safe_call(call_fn)
    
    def append_content(self, filepath: str, content: str) -> Any:
        clean_path = filepath.strip("/")
        url = f"{self.get_base_url()}/vault/{clean_path}"
        
        def call_fn():
            response = requests.post(
                url, 
                headers=self._get_headers() | {'Content-Type': 'text/markdown'}, 
                data=content,
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            response.raise_for_status()
            return None

        return self._safe_call(call_fn)
    
    def patch_content(self, filepath: str, operation: str, target_type: str, target: str, content: str) -> Any:
        clean_path = filepath.strip("/")
        url = f"{self.get_base_url()}/vault/{clean_path}"
        
        headers = self._get_headers() | {
            'Content-Type': 'text/markdown',
            'Operation': operation,
            'Target-Type': target_type,
            'Target': urllib.parse.quote(target)
        }
        
        def call_fn():
            response = requests.patch(url, headers=headers, data=content, verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            return None

        return self._safe_call(call_fn)

    def put_content(self, filepath: str, content: str) -> Any:
        clean_path = filepath.strip("/")
        url = f"{self.get_base_url()}/vault/{clean_path}"
        
        def call_fn():
            response = requests.put(
                url, 
                headers=self._get_headers() | {'Content-Type': 'text/markdown'}, 
                data=content,
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            response.raise_for_status()
            return None

        return self._safe_call(call_fn)
    
    def delete_file(self, filepath: str) -> Any:
        """Delete a file or directory from the vault.
        
        Args:
            filepath: Path to the file to delete (relative to vault root)
            
        Returns:
            None on success
        """
        clean_path = filepath.strip("/")
        url = f"{self.get_base_url()}/vault/{clean_path}"
        
        def call_fn():
            response = requests.delete(url, headers=self._get_headers(), verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            return None
            
        return self._safe_call(call_fn)
    
    def search_json(self, query: dict) -> Any:
        url = f"{self.get_base_url()}/search/"
        
        headers = self._get_headers() | {
            'Content-Type': 'application/vnd.olrapi.jsonlogic+json'
        }
        
        def call_fn():
            response = requests.post(url, headers=headers, json=query, verify=self.verify_ssl, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        return self._safe_call(call_fn)
    
    def get_periodic_note(self, period: str, type: str = "content") -> Any:
        """Get current periodic note for the specified period.
        
        Args:
            period: The period type (daily, weekly, monthly, quarterly, yearly)
            type: Type of the data to get ('content' or 'metadata'). 
                'content' returns just the content in Markdown format. 
                'metadata' includes note metadata (including paths, tags, etc.) and the content.. 
            
        Returns:
            Content of the periodic note
        """
        url = f"{self.get_base_url()}/periodic/{period}/"
        
        def call_fn():
            headers = self._get_headers()
            if type == "metadata":
                headers['Accept'] = 'application/vnd.olrapi.note+json'
            response = requests.get(url, headers=headers, verify=self.verify_ssl, timeout=self.timeout)
            
            # FIX: Handle 404 gracefully
            if response.status_code == 404:
                 return f"Periodic note ({period}) does not exist yet. You can create it using obsidian_put_periodic_note."
                 
            response.raise_for_status()
            
            return response.text

        return self._safe_call(call_fn)

    def put_periodic_note(self, period: str, content: str) -> Any:
        """Create or update the periodic note for the current period (e.g. today).
        
        Args:
            period: The period type (daily, weekly, monthly, quarterly, yearly)
            content: The content to write to the note
            
        Returns:
            None on success
        """
        url = f"{self.get_base_url()}/periodic/{period}/"
        
        def call_fn():
            response = requests.put(
                url, 
                headers=self._get_headers() | {'Content-Type': 'text/markdown'}, 
                data=content,
                verify=self.verify_ssl, 
                timeout=self.timeout
            )
            response.raise_for_status()
            return None

        return self._safe_call(call_fn)
    
    def get_recent_periodic_notes(self, period: str, limit: int = 5, include_content: bool = False) -> Any:
        """Get most recent periodic notes for the specified period type.
        
        Note: This implementation uses Dataview DQL to find files with a valid date.
        
        Args:
            period: The period type (daily, weekly, monthly, quarterly, yearly)
            limit: Maximum number of notes to return (default: 5)
            include_content: Whether to include note content (default: False)
            
        Returns:
            List of recent periodic notes
        """
        # We must use standard TABLE queries, not WITHOUT ID, as the API forbids it.
        # file.day is a built-in Dataview field for periodic notes.
        dql_query = f"""
        TABLE file.day as "date"
        WHERE file.day
        SORT file.day DESC
        LIMIT {limit}
        """

        url = f"{self.get_base_url()}/search/"
        headers = self._get_headers() | {
            'Content-Type': 'application/vnd.olrapi.dataview.dql+txt'
        }
        
        def call_fn():
            # 1. Search for files
            response = requests.post(
                url, 
                headers=headers, 
                data=dql_query.encode('utf-8'),
                verify=self.verify_ssl, 
                timeout=self.timeout
            )
            response.raise_for_status()
            results = response.json()
            
            # 2. Format results
            formatted_results = []
            for item in results:
                # The API returns dicts with 'filename' (implicit ID) and 'result' (columns)
                filepath = item.get("filename", "Unknown")
                
                # 'result' contains the requested columns
                result_data = item.get("result", {})
                date = result_data.get("date", "Unknown") if isinstance(result_data, dict) else "Unknown"

                note_info = {
                    "filepath": filepath,
                    "date": date
                }
                
                # 3. Fetch content if requested
                if include_content:
                    try:
                        content = self.get_file_contents(filepath)
                        note_info["content"] = content
                    except Exception:
                        note_info["content"] = "<Error fetching content>"
                
                formatted_results.append(note_info)
                
            return formatted_results

        return self._safe_call(call_fn)
    
    def get_recent_changes(self, limit: int = 10, days: int = 90) -> Any:
        """Get recently modified files in the vault.
        
        Args:
            limit: Maximum number of files to return (default: 10)
            days: Only include files modified within this many days (default: 90)
            
        Returns:
            List of recently modified files with metadata
        """
        # Build the DQL query
        query_lines = [
            "TABLE file.mtime",
            f"WHERE file.mtime >= date(today) - dur({days} days)",
            "SORT file.mtime DESC",
            f"LIMIT {limit}"
        ]
        
        # Join with proper DQL line breaks
        dql_query = "\n".join(query_lines)
        
        # Make the request to search endpoint
        url = f"{self.get_base_url()}/search/"
        headers = self._get_headers() | {
            'Content-Type': 'application/vnd.olrapi.dataview.dql+txt'
        }
        
        def call_fn():
            response = requests.post(
                url,
                headers=headers,
                data=dql_query.encode('utf-8'),
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

        return self._safe_call(call_fn)
