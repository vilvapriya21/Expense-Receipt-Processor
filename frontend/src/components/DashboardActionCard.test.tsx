import UploadFileIcon from "@mui/icons-material/UploadFile";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { DashboardActionCard } from "@/components/DashboardActionCard";

describe("DashboardActionCard", () => {
  it("renders its workflow copy and destination", () => {
    render(
      <MemoryRouter>
        <DashboardActionCard
          title="Upload a receipt"
          description="Extract expense details."
          to="/employee/upload"
          icon={<UploadFileIcon />}
        />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: /upload a receipt/i })).toHaveAttribute(
      "href",
      "/employee/upload",
    );
    expect(screen.getByText("Extract expense details.")).toBeInTheDocument();
  });
});
